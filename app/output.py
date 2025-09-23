"""Utilities for injecting recognised text into the active application."""
from __future__ import annotations

import logging
import platform
import time
from dataclasses import dataclass
from typing import Optional

from .config import OutputConfig

try:  # pragma: no cover - optional dependency
    import pyautogui
except ImportError:  # pragma: no cover
    pyautogui = None  # type: ignore

try:  # pragma: no cover - optional dependency
    import pyperclip
except ImportError:  # pragma: no cover
    pyperclip = None  # type: ignore

try:  # pragma: no cover - optional dependency
    from plyer import notification
except ImportError:  # pragma: no cover
    notification = None  # type: ignore


_LOGGER = logging.getLogger(__name__)


@dataclass
class OutputDispatcher:
    """Handles post-processing and delivery of recognised text."""

    config: OutputConfig
    clipboard: Optional[object] = None
    gui: Optional[object] = None

    def __post_init__(self) -> None:
        if self.clipboard is None:
            self.clipboard = pyperclip
        if self.gui is None:
            self.gui = pyautogui

    def _apply_text_rules(self, text: str) -> str:
        text = text.strip()
        if not text:
            return text
        if self.config.auto_capitalise and text:
            text = text[0].upper() + text[1:]
        if self.config.auto_punctuation and text and text[-1] not in ".?!":
            text = f"{text}."
        return text

    def send_text(self, text: str) -> None:
        text = self._apply_text_rules(text)
        if not text:
            _LOGGER.debug("Ignoring empty transcription result")
            return
        if self.config.method == "clipboard":
            self._send_via_clipboard(text)
        elif self.config.method == "type":
            self._type_text(text)
        else:
            raise ValueError(f"Unsupported output method: {self.config.method}")

    # ------------------------------------------------------------------
    # Clipboard delivery
    # ------------------------------------------------------------------
    def _send_via_clipboard(self, text: str) -> None:
        if self.clipboard is None or self.gui is None:
            raise RuntimeError(
                "pyperclip and pyautogui are required for clipboard injection"
            )
        previous_value = None
        if self.config.restore_clipboard:
            try:
                previous_value = self.clipboard.paste()
            except Exception as exc:  # pragma: no cover - platform dependent
                _LOGGER.warning("Failed to read clipboard: %s", exc)
        try:
            self.clipboard.copy(text)
            modifier = "command" if platform.system() == "Darwin" else "ctrl"
            self.gui.hotkey(modifier, "v")
            _LOGGER.info("Sent transcription via clipboard")
        finally:
            if self.config.restore_clipboard and previous_value is not None:
                time.sleep(0.05)
                try:
                    self.clipboard.copy(previous_value)
                except Exception as exc:  # pragma: no cover - platform dependent
                    _LOGGER.warning("Failed to restore clipboard: %s", exc)

    # ------------------------------------------------------------------
    # Typing delivery
    # ------------------------------------------------------------------
    def _type_text(self, text: str) -> None:
        if self.gui is None:
            raise RuntimeError("pyautogui must be installed for typing output")
        self.gui.typewrite(text)
        _LOGGER.info("Typed transcription into active window")

    # ------------------------------------------------------------------
    # Notifications
    # ------------------------------------------------------------------
    def notify(self, title: str, message: str) -> None:
        if not self.config.fallback_notification:
            return
        if notification is None:  # pragma: no cover - optional dependency
            _LOGGER.info("Notification requested but plyer is not installed")
            return
        try:  # pragma: no cover - platform behaviour
            notification.notify(title=title, message=message, app_name="Whisper Flow")
        except Exception as exc:
            _LOGGER.warning("Failed to display notification: %s", exc)


__all__ = ["OutputDispatcher"]
