"""Realtime transcription pipeline built on top of Whisper."""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional, Sequence

from .audio import AudioSource, AudioSourceFactory, MicrophoneAudioSource
from .config import AppConfig
from .output import OutputDispatcher

try:  # pragma: no cover - optional dependency
    import numpy as np
except ImportError:  # pragma: no cover
    np = None  # type: ignore

try:  # pragma: no cover - optional dependency
    import whisper
except ImportError:  # pragma: no cover
    whisper = None  # type: ignore


_LOGGER = logging.getLogger(__name__)


@dataclass
class TranscriptionResult:
    text: str
    segments: Sequence[dict]
    duration: float


ResultCallback = Callable[[TranscriptionResult], None]


class WhisperTranscriber:
    """Manage microphone capture, Whisper inference and text delivery."""

    def __init__(
        self,
        config: AppConfig,
        *,
        audio_source_factory: Optional[AudioSourceFactory] = None,
        model_loader: Optional[Callable[[], object]] = None,
        output: Optional[OutputDispatcher] = None,
        on_result: Optional[ResultCallback] = None,
    ) -> None:
        self._config = config
        self._audio_source_factory = audio_source_factory
        self._model_loader = model_loader or self._default_model_loader
        self._output = output or OutputDispatcher(config.output)
        self._on_result = on_result
        self._model: Optional[object] = None
        self._audio_source: Optional[AudioSource] = None
        self._worker: Optional[threading.Thread] = None
        self._running = threading.Event()
        self._last_audio: Optional[Sequence[float]] = None
        self._last_result: Optional[TranscriptionResult] = None
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Lifecycle management
    # ------------------------------------------------------------------
    def start(self) -> None:
        if self._running.is_set():
            return
        self._ensure_model()
        self._audio_source = self._create_audio_source()
        self._audio_source.start()
        self._running.set()
        self._worker = threading.Thread(target=self._run_loop, daemon=True)
        self._worker.start()
        _LOGGER.info("Listening for speech…")

    def stop(self) -> None:
        self._running.clear()
        if self._worker is not None:
            self._worker.join(timeout=5)
            self._worker = None
        if self._audio_source is not None:
            self._audio_source.stop()
            self._audio_source = None
        _LOGGER.info("Stopped listening")

    def toggle(self) -> None:
        if self._running.is_set():
            self.stop()
        else:
            self.start()

    def retry_last(self) -> Optional[TranscriptionResult]:
        if self._last_audio is None:
            _LOGGER.info("There is no previous audio to retry")
            return None
        _LOGGER.info("Retrying last transcription")
        result = self._transcribe_audio(self._last_audio, store_history=False)
        if result is not None:
            self._last_result = result
            if self._on_result is not None:
                self._on_result(result)
            self._output.send_text(result.text)
        return result

    @property
    def last_result(self) -> Optional[TranscriptionResult]:
        return self._last_result

    @property
    def is_listening(self) -> bool:
        """Return ``True`` when audio capture is active."""

        return self._running.is_set()

    @property
    def output(self) -> OutputDispatcher:
        """Expose the output dispatcher (useful for UI components)."""

        return self._output

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _create_audio_source(self) -> AudioSource:
        if self._audio_source_factory is not None:
            return self._audio_source_factory()
        return MicrophoneAudioSource(self._config.audio)

    def _ensure_model(self) -> None:
        with self._lock:
            if self._model is not None:
                return
            self._model = self._model_loader()
            _LOGGER.info("Loaded Whisper model")

    def _default_model_loader(self):  # pragma: no cover - requires whisper
        if whisper is None:
            raise RuntimeError("The 'whisper' package is required for transcription")
        return whisper.load_model(self._config.transcription.model_size)

    def _run_loop(self) -> None:
        assert self._audio_source is not None
        config = self._config.audio
        silence_blocks = max(
            1,
            int(
                (config.silence_duration * config.sample_rate)
                / max(config.block_size, 1)
            ),
        )
        min_samples = int(config.min_duration * config.sample_rate)
        buffer: list = []
        silence_counter = 0
        while self._running.is_set():
            chunk = self._audio_source.read(timeout=0.2)
            if chunk is None:
                if buffer:
                    silence_counter += 1
                    if silence_counter >= silence_blocks:
                        self._handle_buffer(buffer)
                        buffer = []
                        silence_counter = 0
                continue
            amplitude = self._estimate_amplitude(chunk)
            if amplitude < config.silence_threshold and not buffer:
                continue
            buffer.append(self._as_array(chunk))
            if self._count_samples(buffer) < min_samples:
                continue
            silence_counter = 0
        if buffer:
            self._handle_buffer(buffer)

    def _handle_buffer(self, buffer: list) -> None:
        audio = self._concatenate(buffer)
        result = self._transcribe_audio(audio)
        if result is None:
            return
        self._last_audio = audio
        self._last_result = result
        if self._on_result is not None:
            self._on_result(result)
        self._output.send_text(result.text)

    def _transcribe_audio(
        self, audio, *, store_history: bool = True
    ) -> Optional[TranscriptionResult]:
        if self._model is None:
            self._ensure_model()
        if self._model is None:
            raise RuntimeError("Failed to load Whisper model")
        config = self._config.transcription
        start = time.time()
        try:
            raw = self._model.transcribe(
                audio,
                language=config.language,
                temperature=config.temperature,
                beam_size=config.beam_size,
                best_of=config.best_of,
                condition_on_previous_text=config.condition_on_previous_text,
                initial_prompt=config.initial_prompt,
            )
        except Exception as exc:  # pragma: no cover - depends on model
            _LOGGER.exception("Transcription failed: %s", exc)
            self._output.notify("Whisper", "Transcription failed. Check logs for details.")
            return None
        duration = time.time() - start
        text = (raw.get("text") or "").strip()
        segments = raw.get("segments") or []
        result = TranscriptionResult(text=text, segments=segments, duration=duration)
        _LOGGER.info("Transcription complete in %.2fs: %s", duration, text)
        if store_history:
            self._last_audio = audio
            self._last_result = result
        return result

    # ------------------------------------------------------------------
    # Utility functions
    # ------------------------------------------------------------------
    def _as_array(self, chunk):
        if np is None:
            if isinstance(chunk, (list, tuple)):
                return [float(x) for x in chunk]
            return [float(chunk)]
        if isinstance(chunk, np.ndarray):
            return chunk.astype("float32", copy=False)
        return np.asarray(chunk, dtype="float32")

    def _concatenate(self, chunks):
        if np is None:
            data = []
            for chunk in chunks:
                data.extend(float(x) for x in chunk)
            return data
        return np.concatenate(chunks).astype("float32")

    def _count_samples(self, chunks) -> int:
        if np is None:
            return sum(len(chunk) for chunk in chunks)
        return int(sum(chunk.size for chunk in chunks))

    def _estimate_amplitude(self, chunk) -> float:
        if np is None:
            if isinstance(chunk, (list, tuple)) and chunk:
                return float(max(abs(x) for x in chunk))
            return 0.0
        arr = self._as_array(chunk)
        return float(np.max(np.abs(arr)))


__all__ = ["TranscriptionResult", "WhisperTranscriber"]
