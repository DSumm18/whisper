import os
from pathlib import Path
import tempfile
import unittest

from app.output import (
    InjectionError,
    OutputManager,
    normalise_transcript,
)


class DummyInjector:
    def __init__(self, succeed: bool = True) -> None:
        self.succeed = succeed
        self.calls = []

    def __call__(self, text: str) -> None:
        self.calls.append(text)
        if not self.succeed:
            raise InjectionError("simulated failure")


class OutputManagerTests(unittest.TestCase):
    def test_normalise_transcript_preserves_unicode_and_trims(self) -> None:
        text = "  Héllo\r\ncolourful organisation  "
        self.assertEqual(normalise_transcript(text), "Héllo\ncolourful organisation")

    def test_send_transcript_uses_first_successful_injector(self) -> None:
        injector = DummyInjector()
        fallback_calls: list[str] = []

        def fallback(text: str) -> Path:
            fallback_calls.append(text)
            path = Path(tempfile.gettempdir()) / "fallback.txt"
            path.write_text(text, encoding="utf-8")
            return path

        manager = OutputManager(
            injectors_factory=lambda: [injector],
            overlay_editor=lambda text: text,
            fallback_handler=fallback,
        )

        result = manager.send_transcript(" Hello world \n ")

        self.assertEqual(result, "Hello world")
        self.assertEqual(injector.calls, ["Hello world"])
        self.assertEqual(fallback_calls, [])

    def test_send_transcript_falls_back_when_all_injectors_fail(self) -> None:
        failing = DummyInjector(succeed=False)
        fallback_calls: list[str] = []

        with tempfile.TemporaryDirectory() as tmp:
            os.environ["WHISPER_OUTPUT_FALLBACK_PATH"] = str(Path(tmp) / "fallback.txt")

            def fallback(text: str) -> Path:
                fallback_calls.append(text)
                path = Path(os.environ["WHISPER_OUTPUT_FALLBACK_PATH"])
                path.write_text(text, encoding="utf-8")
                return path

            manager = OutputManager(
                injectors_factory=lambda: [failing],
                overlay_editor=lambda text: text,
                fallback_handler=fallback,
            )

            result = manager.send_transcript("   test text   ")

            self.assertEqual(result, "test text")
            self.assertEqual(fallback_calls, ["test text"])

            stored = Path(os.environ["WHISPER_OUTPUT_FALLBACK_PATH"])
            self.assertTrue(stored.exists())
            self.assertEqual(stored.read_text(encoding="utf-8"), "test text")

        os.environ.pop("WHISPER_OUTPUT_FALLBACK_PATH", None)

    def test_repeat_last_sentence_uses_history(self) -> None:
        injector = DummyInjector()
        manager = OutputManager(
            injectors_factory=lambda: [injector],
            overlay_editor=lambda text: text,
            fallback_handler=lambda text: Path(tempfile.gettempdir()) / "fallback.txt",
        )

        manager.send_transcript("First line")
        manager.send_transcript("Second line")

        repeat = manager.repeat_last_sentence()

        self.assertEqual(repeat, "Second line")
        self.assertEqual(injector.calls[-2:], ["Second line", "Second line"])

    def test_quick_edit_uses_overlay_callable(self) -> None:
        injector = DummyInjector()

        def overlay(text: str) -> str:
            return text + " (edited)"

        manager = OutputManager(
            injectors_factory=lambda: [injector],
            overlay_editor=overlay,
            fallback_handler=lambda text: Path(tempfile.gettempdir()) / "fallback.txt",
        )

        manager.send_transcript("Original", quick_edit=True)

        self.assertEqual(injector.calls, ["Original (edited)"])

    def test_repeat_without_history_returns_none(self) -> None:
        manager = OutputManager(
            injectors_factory=lambda: [],
            overlay_editor=lambda text: text,
            fallback_handler=lambda text: Path(tempfile.gettempdir()) / "fallback.txt",
        )

        self.assertIsNone(manager.repeat_last_sentence())


if __name__ == "__main__":  # pragma: no cover - manual execution
    unittest.main()
