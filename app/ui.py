"""System tray UI for the Whisper desktop assistant."""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from typing import Optional

from .config import AppConfig
from .hotkeys import HotkeyController
from .output import OutputDispatcher
from .transcriber import TranscriptionResult, WhisperTranscriber

try:  # pragma: no cover - optional dependency
    import pystray
    from PIL import Image, ImageDraw
except ImportError:  # pragma: no cover
    pystray = None  # type: ignore
    Image = None  # type: ignore
    ImageDraw = None  # type: ignore


_LOGGER = logging.getLogger(__name__)


@dataclass
class VoiceTypingApp:
    """Container wiring together the UI, hotkeys and transcriber."""

    config: AppConfig
    transcriber: Optional[WhisperTranscriber] = None
    output: Optional[OutputDispatcher] = None

    def __post_init__(self) -> None:
        if self.transcriber is None:
            self.transcriber = WhisperTranscriber(
                self.config,
                output=self.output,
                on_result=self._handle_result,
            )
        self.output = self.transcriber.output  # reuse dispatcher
        self._icon: Optional[pystray.Icon] = None
        self._state = "idle"
        self._notification_lock = threading.Lock()
        self._setup_hotkeys()
        self._setup_tray_icon()

    # ------------------------------------------------------------------
    # Application bootstrap
    # ------------------------------------------------------------------
    def _setup_hotkeys(self) -> None:
        try:
            controller = HotkeyController(
                self.config.hotkey,
                on_toggle=self._toggle_from_hotkey,
                on_start=self._start_from_hotkey,
                on_stop=self._stop_from_hotkey,
            )
            controller.register()
            self._hotkey_controller = controller
        except Exception as exc:
            self._hotkey_controller = None
            _LOGGER.warning("Unable to register global hotkeys: %s", exc)

    def _setup_tray_icon(self) -> None:
        if pystray is None or Image is None:
            _LOGGER.warning("pystray or Pillow not installed; running without tray icon")
            return
        icon_image = self._build_icon("idle")
        menu = pystray.Menu(
            pystray.MenuItem("Start listening", lambda: self._defer(self.start)),
            pystray.MenuItem("Stop listening", lambda: self._defer(self.stop)),
            pystray.MenuItem("Retry last", lambda: self._defer(self.retry_last)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", lambda: self._defer(self.shutdown)),
        )
        self._icon = pystray.Icon("whisper-flow", icon_image, "Whisper Flow", menu)

    def run(self) -> None:
        if self._icon is not None:
            self._icon.run()
        else:
            self.start()
            self._run_cli_loop()

    # ------------------------------------------------------------------
    # Tray helpers
    # ------------------------------------------------------------------
    def _build_icon(self, state: str):  # pragma: no cover - UI drawing
        if Image is None or ImageDraw is None:
            raise RuntimeError("Pillow is required to draw the tray icon")
        size = 64
        image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        colours = {
            "idle": (120, 120, 120, 255),
            "listening": (20, 160, 240, 255),
            "transcribing": (220, 160, 0, 255),
        }
        colour = colours.get(state, colours["idle"])
        draw.ellipse((8, 8, size - 8, size - 8), fill=colour)
        draw.text((size // 3, size // 3), "W", fill=(255, 255, 255, 255))
        return image

    def _update_icon(self, state: str) -> None:
        self._state = state
        if self._icon is None:
            return
        self._icon.icon = self._build_icon(state)
        self._icon.title = f"Whisper Flow – {state.title()}"

    def _defer(self, func):
        def wrapper():
            threading.Thread(target=func, daemon=True).start()

        return wrapper

    def _run_cli_loop(self) -> None:  # pragma: no cover - interactive loop
        _LOGGER.info("Voice typing running without tray icon. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.shutdown()

    # ------------------------------------------------------------------
    # Hotkey callbacks
    # ------------------------------------------------------------------
    def _toggle_from_hotkey(self) -> None:
        if self.transcriber is None:
            return
        self.transcriber.toggle()
        self._update_icon("listening" if self.transcriber.is_listening else "idle")

    def _start_from_hotkey(self) -> None:
        if self.transcriber is None:
            return
        self.transcriber.start()
        self._update_icon("listening")

    def _stop_from_hotkey(self) -> None:
        if self.transcriber is None:
            return
        self.transcriber.stop()
        self._update_icon("idle")

    # ------------------------------------------------------------------
    # Public actions exposed via the tray menu
    # ------------------------------------------------------------------
    def start(self) -> None:
        if self.transcriber is None:
            return
        self.transcriber.start()
        self._update_icon("listening")

    def stop(self) -> None:
        if self.transcriber is None:
            return
        self.transcriber.stop()
        self._update_icon("idle")

    def retry_last(self) -> None:
        if self.transcriber is None:
            return
        result = self.transcriber.retry_last()
        if result is None:
            self._notify("Nothing to retry")
        else:
            self._notify(f"Retried: {result.text}")

    def shutdown(self) -> None:
        if self.transcriber is not None:
            self.transcriber.stop()
        if self._icon is not None:
            self._icon.stop()

    # ------------------------------------------------------------------
    # Result handling
    # ------------------------------------------------------------------
    def _handle_result(self, result: TranscriptionResult) -> None:
        self._update_icon("transcribing")
        self._notify(result.text)
        self._update_icon("listening")

    def _notify(self, message: str) -> None:
        if not message or self.output is None:
            return
        if not self.config.ui.show_notifications:
            return
        with self._notification_lock:
            self.output.notify("Whisper", message)


__all__ = ["VoiceTypingApp"]
