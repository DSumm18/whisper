"""Audio capture helpers for the Whisper desktop assistant."""
from __future__ import annotations

import logging
import queue
import threading
import time
from dataclasses import dataclass
from typing import Callable, Iterable, Optional

from .config import AudioConfig

try:  # pragma: no cover - optional dependency
    import numpy as np
except ImportError:  # pragma: no cover
    np = None  # type: ignore

try:  # pragma: no cover - optional dependency
    import sounddevice as sd
except ImportError:  # pragma: no cover
    sd = None  # type: ignore


_LOGGER = logging.getLogger(__name__)


class AudioSource:
    """Abstract base class representing a pull-based audio source."""

    def start(self) -> "AudioSource":  # pragma: no cover - interface definition
        raise NotImplementedError

    def read(self, timeout: float = 0.1):  # pragma: no cover - interface definition
        raise NotImplementedError

    def stop(self) -> None:  # pragma: no cover - interface definition
        raise NotImplementedError


class MicrophoneAudioSource(AudioSource):
    """Capture PCM audio from the system microphone using sounddevice."""

    def __init__(self, config: AudioConfig):
        if sd is None or np is None:  # pragma: no cover - requires optional deps
            raise RuntimeError(
                "sounddevice and numpy must be installed to use the microphone source"
            )
        self._config = config
        self._queue: "queue.Queue[np.ndarray]" = queue.Queue()
        self._stream: Optional[sd.InputStream] = None
        self._lock = threading.Lock()
        self._running = False

    def _callback(self, indata, frames, time_info, status):  # pragma: no cover - IO
        if status:
            _LOGGER.warning("Microphone status: %s", status)
        self._queue.put(indata.copy())

    def start(self) -> "MicrophoneAudioSource":
        with self._lock:
            if self._running:
                return self
            self._running = True
            self._queue = queue.Queue()
            self._stream = sd.InputStream(
                samplerate=self._config.sample_rate,
                channels=1,
                dtype="float32",
                callback=self._callback,
                blocksize=self._config.block_size,
                device=self._config.input_device,
            )
            self._stream.start()
        return self

    def read(self, timeout: float = 0.1):
        try:
            chunk = self._queue.get(timeout=timeout)
        except queue.Empty:
            return None
        return chunk.reshape(-1)

    def stop(self) -> None:
        with self._lock:
            self._running = False
            if self._stream is not None:
                try:
                    self._stream.stop()
                    self._stream.close()
                finally:
                    self._stream = None
            # drain queue to release waiting threads
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                except queue.Empty:  # pragma: no cover - defensive
                    break


@dataclass
class IterableAudioSource(AudioSource):
    """Audio source backed by a Python iterable of numpy arrays.

    Primarily used for testing where deterministic control of the audio stream is
    required.  The iterable can yield numpy arrays or ``None`` to simulate
    periods of silence.
    """

    iterable: Iterable
    repeat_last: bool = False

    def __post_init__(self) -> None:
        self._iterator = iter(self.iterable)
        self._last = None

    def start(self) -> "IterableAudioSource":
        return self

    def read(self, timeout: float = 0.1):  # pragma: no cover - trivial
        try:
            value = next(self._iterator)
        except StopIteration:
            if self.repeat_last:
                time.sleep(timeout)
                return self._last
            time.sleep(timeout)
            return None
        self._last = value
        return value

    def stop(self) -> None:  # pragma: no cover - nothing to clean up
        pass


AudioSourceFactory = Callable[[], AudioSource]


__all__ = [
    "AudioSource",
    "AudioSourceFactory",
    "IterableAudioSource",
    "MicrophoneAudioSource",
]
