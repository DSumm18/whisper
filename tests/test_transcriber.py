import time

from app.audio import IterableAudioSource
from app.config import AppConfig
from app.transcriber import TranscriptionResult, WhisperTranscriber


class DummyModel:
    def __init__(self, text="hello world"):
        self.text = text
        self.calls = []

    def transcribe(self, audio, **kwargs):
        self.calls.append((audio, kwargs))
        return {"text": self.text, "segments": []}


class CaptureOutput:
    def __init__(self):
        self.messages = []

    def send_text(self, text):
        self.messages.append(text)

    def notify(self, title, message):
        self.messages.append(f"notify:{title}:{message}")


def _make_chunk(length: int, value: float):
    return [value] * length


def test_transcriber_processes_iterable_source():
    config = AppConfig.default()
    config.audio.block_size = 4000
    config.audio.min_duration = 0.05
    config.audio.silence_duration = 0.05
    dummy_audio = [
        _make_chunk(config.audio.block_size, 0.1),
        _make_chunk(config.audio.block_size, 0.1),
        None,
        None,
    ]
    output = CaptureOutput()
    model = DummyModel("dictated text")

    transcriber = WhisperTranscriber(
        config,
        audio_source_factory=lambda: IterableAudioSource(dummy_audio),
        model_loader=lambda: model,
        output=output,
    )

    transcriber.start()
    time.sleep(0.3)
    transcriber.stop()

    assert any("dictated text" in message for message in output.messages)
    assert isinstance(transcriber.last_result, TranscriptionResult)
    assert model.calls, "model should have been invoked"


def test_retry_last_replays_audio():
    config = AppConfig.default()
    config.audio.block_size = 4000
    config.audio.min_duration = 0.05
    config.audio.silence_duration = 0.05
    dummy_audio = [
        _make_chunk(config.audio.block_size, 0.2),
        None,
        None,
    ]
    output = CaptureOutput()
    model = DummyModel("first pass")

    transcriber = WhisperTranscriber(
        config,
        audio_source_factory=lambda: IterableAudioSource(dummy_audio),
        model_loader=lambda: model,
        output=output,
    )

    transcriber.start()
    time.sleep(0.2)
    transcriber.stop()

    model.text = "retry pass"
    result = transcriber.retry_last()

    assert result is not None
    assert result.text == "retry pass"
    assert any("retry pass" in message for message in output.messages)
