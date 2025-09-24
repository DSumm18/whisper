"""Utilities for producing audible feedback for the tray UI."""

from __future__ import annotations

import logging
import os
import platform
import shutil
import subprocess
import sys
import threading
from dataclasses import dataclass

from .transcriber import TranscriberState

LOGGER = logging.getLogger(__name__)


@dataclass
class FeedbackTone:
    frequency: int
    duration_ms: int
    repeat: int = 1


DEFAULT_TONES = {
    TranscriberState.LISTENING: FeedbackTone(880, 120),
    TranscriberState.TRANSCRIBING: FeedbackTone(660, 120, repeat=2),
    TranscriberState.ERROR: FeedbackTone(220, 300, repeat=2),
}


class FeedbackPlayer:
    """Plays simple beeps using platform-specific mechanisms."""

    def __init__(self) -> None:
        self._lock = threading.Lock()

    def play(self, state: TranscriberState) -> None:
        tone = DEFAULT_TONES.get(state)
        if not tone:
            return
        threading.Thread(target=self._play_tone, args=(tone,), daemon=True).start()

    def _play_tone(self, tone: FeedbackTone) -> None:
        with self._lock:
            for _ in range(tone.repeat):
                try:
                    self._beep(tone.frequency, tone.duration_ms)
                except Exception:  # pragma: no cover - platform specific fallback
                    LOGGER.exception("Failed to play feedback tone")
                    break

    @staticmethod
    def _beep(frequency: int, duration_ms: int) -> None:
        system = platform.system().lower()
        if system == "windows":
            import winsound

            winsound.Beep(frequency, duration_ms)
            return

        if system == "darwin":
            subprocess.run(["osascript", "-e", "beep"], check=False)
            return

        if shutil.which("play"):
            subprocess.run(
                [
                    "play",
                    "-nq",
                    "-t",
                    "alsa",
                    "synth",
                    str(duration_ms / 1000.0),
                    "sin",
                    str(frequency),
                ],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return

        if shutil.which("beep"):
            subprocess.run(
                ["beep", "-f", str(frequency), "-l", str(duration_ms)],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return

        sys.stdout.write("\a")
        sys.stdout.flush()
        try:
            fd = sys.stdout.fileno()
            os.fsync(fd)
        except (AttributeError, OSError):
            pass
