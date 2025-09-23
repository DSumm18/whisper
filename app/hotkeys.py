"""Global hotkey management for the Whisper assistant."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, Optional

from .config import HotkeyConfig

try:  # pragma: no cover - optional dependency
    import keyboard
except ImportError:  # pragma: no cover
    keyboard = None  # type: ignore

try:  # pragma: no cover - optional dependency
    import mouse
except ImportError:  # pragma: no cover
    mouse = None  # type: ignore


_LOGGER = logging.getLogger(__name__)


Callback = Callable[[], None]


@dataclass
class HotkeyController:
    """Wires global hotkeys to call into the transcription engine."""

    config: HotkeyConfig
    on_toggle: Optional[Callback] = None
    on_start: Optional[Callback] = None
    on_stop: Optional[Callback] = None

    def register(self) -> None:
        if self.config.toggle_key and self.on_toggle is not None:
            if keyboard is None:
                raise RuntimeError("The 'keyboard' package is required for hotkeys")
            keyboard.add_hotkey(self.config.toggle_key, self._safe_call(self.on_toggle))
            _LOGGER.info("Registered toggle hotkey: %s", self.config.toggle_key)
        if self.config.push_to_talk:
            if keyboard is None:
                raise RuntimeError("The 'keyboard' package is required for hotkeys")
            keyboard.on_press_key(
                self.config.push_to_talk,
                lambda _: self._safe_call(self.on_start)(),
            )
            keyboard.on_release_key(
                self.config.push_to_talk,
                lambda _: self._safe_call(self.on_stop)(),
            )
            _LOGGER.info("Registered push-to-talk key: %s", self.config.push_to_talk)
        if self.config.mouse_button and mouse is not None and self.on_toggle is not None:
            mouse.on_button(
                lambda event: self._handle_mouse(event),
                buttons=(self.config.mouse_button,),
                types=("down",),
            )
            _LOGGER.info("Registered mouse toggle: %s", self.config.mouse_button)

    def _safe_call(self, func: Optional[Callback]) -> Callback:
        def wrapper() -> None:
            if func is None:
                return
            try:
                func()
            except Exception:  # pragma: no cover - defensive logging
                _LOGGER.exception("Hotkey callback raised an exception")

        return wrapper

    def _handle_mouse(self, event) -> None:  # pragma: no cover - requires hardware
        if event.event_type != "down":
            return
        if self.on_toggle is None:
            return
        self._safe_call(self.on_toggle)()


__all__ = ["HotkeyController"]
