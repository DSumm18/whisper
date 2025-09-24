"""Desktop tray user interface for controlling the transcriber service."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from typing import Dict, Optional

import keyboard
import mouse
import pystray
from PIL import Image, ImageDraw

from .config import Settings
from .feedback import FeedbackPlayer
from .transcriber import TranscriberService, TranscriberState

LOGGER = logging.getLogger(__name__)

ICON_SIZE = (64, 64)
ICON_COLORS = {
    TranscriberState.STOPPED: "#4b5563",  # slate grey
    TranscriberState.LISTENING: "#2563eb",  # blue
    TranscriberState.TRANSCRIBING: "#16a34a",  # green
    TranscriberState.ERROR: "#dc2626",  # red
}


class TrayApplication:
    """System tray application binding hotkeys to the transcriber service."""

    def __init__(self, service: TranscriberService, settings: Settings) -> None:
        self.service = service
        self.settings = settings
        self.feedback = FeedbackPlayer()
        self._keyboard_handle: Optional[int] = None
        self._mouse_handler: Optional[Callable[[object], None]] = None
        self._icons: Dict[TranscriberState, Image.Image] = self._generate_icons()
        self._status_text = self._format_status(TranscriberState.STOPPED)
        self._menu_lock = threading.Lock()

        self.icon = pystray.Icon(
            name="Whisper",
            icon=self._icons[TranscriberState.STOPPED],
            title=self._tooltip_for_state(TranscriberState.STOPPED),
            menu=self._build_menu(),
        )
        self.service.register_state_callback(self._on_state_change)

    def run(self) -> None:
        """Start the tray application."""

        LOGGER.info("Launching tray icon")
        self.icon.run(setup=self._setup)

    def stop(self) -> None:
        """Stop the tray application and unregister hotkeys."""

        LOGGER.info("Stopping tray icon")
        self._unregister_hotkeys()
        try:
            self.service.stop()
        finally:
            self.icon.visible = False
            self.icon.stop()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _setup(self, _icon: pystray.Icon) -> None:
        self._register_hotkeys()
        if self.settings.start_on_launch:
            LOGGER.info("Start on launch enabled")
            self.service.start()

    def _build_menu(self) -> pystray.Menu:
        return pystray.Menu(
            pystray.MenuItem(self._status_text, None, enabled=False),
            pystray.MenuItem("Start listening", self._menu_start),
            pystray.MenuItem("Stop listening", self._menu_stop),
            pystray.MenuItem("Quit", self._menu_quit),
        )

    def _generate_icons(self) -> Dict[TranscriberState, Image.Image]:
        icons: Dict[TranscriberState, Image.Image] = {}
        for state, color in ICON_COLORS.items():
            image = Image.new("RGBA", ICON_SIZE, (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            draw.ellipse((8, 8, ICON_SIZE[0] - 8, ICON_SIZE[1] - 8), fill=color)
            icons[state] = image
        return icons

    def _tooltip_for_state(self, state: TranscriberState) -> str:
        return f"Whisper – {state.value.title()}"

    def _format_status(self, state: TranscriberState) -> str:
        return f"Status: {state.value.title()}"

    def _on_state_change(self, state: TranscriberState) -> None:
        LOGGER.info("State changed to %s", state.value)
        self.feedback.play(state)
        with self._menu_lock:
            self._status_text = self._format_status(state)
            self.icon.icon = self._icons[state]
            self.icon.title = self._tooltip_for_state(state)
            self.icon.menu = self._build_menu()
            self.icon.update_menu()

    def _register_hotkeys(self) -> None:
        try:
            self._keyboard_handle = keyboard.add_hotkey(
                self.settings.hotkey, self._handle_toggle, suppress=False
            )
            LOGGER.info("Registered hotkey: %s", self.settings.hotkey)
        except Exception:
            LOGGER.exception("Failed to register keyboard hotkey '%s'", self.settings.hotkey)

        if self.settings.mouse_button:
            button = self._normalise_mouse_button(self.settings.mouse_button)
            if button:
                try:
                    self._mouse_handler = mouse.on_button(
                        self._handle_mouse_toggle, buttons=(button,), types=("down",)
                    )
                    LOGGER.info("Registered mouse button hotkey: %s", button)
                except Exception:
                    LOGGER.exception("Failed to register mouse hotkey '%s'", button)
            else:
                LOGGER.warning("Unsupported mouse button configured: %s", self.settings.mouse_button)

    def _unregister_hotkeys(self) -> None:
        if self._keyboard_handle is not None:
            try:
                keyboard.remove_hotkey(self._keyboard_handle)
                LOGGER.info("Keyboard hotkey removed")
            except Exception:
                LOGGER.exception("Failed to remove keyboard hotkey")
            self._keyboard_handle = None

        if self._mouse_handler is not None:
            try:
                mouse.unhook(self._mouse_handler)
                LOGGER.info("Mouse hotkey removed")
            except Exception:
                LOGGER.exception("Failed to remove mouse hotkey")
            self._mouse_handler = None

    def _handle_toggle(self) -> None:
        LOGGER.info("Hotkey pressed – toggling service")
        state = self.service.toggle()
        if state == TranscriberState.ERROR:
            LOGGER.error("Service entered error state after toggle")

    def _handle_mouse_toggle(self, event: object) -> None:
        if getattr(event, 'event_type', None) != 'down':
            return
        LOGGER.info("Mouse button hotkey pressed – toggling service")
        self._handle_toggle()

    @staticmethod
    def _normalise_mouse_button(button: str) -> Optional[str]:
        mapping = {
            "x1": "x",  # mouse library uses "x" for the first side button
            "x2": "x2",
            "left": "left",
            "right": "right",
            "middle": "middle",
        }
        return mapping.get(button.lower())

    # ------------------------------------------------------------------
    # Menu callbacks
    # ------------------------------------------------------------------
    def _menu_start(self, _: pystray.Icon, __: pystray.MenuItem) -> None:
        LOGGER.info("Start selected from tray menu")
        self.service.start()

    def _menu_stop(self, _: pystray.Icon, __: pystray.MenuItem) -> None:
        LOGGER.info("Stop selected from tray menu")
        self.service.stop()

    def _menu_quit(self, icon: pystray.Icon, _: pystray.MenuItem) -> None:
        LOGGER.info("Quit selected from tray menu")
        self.stop()

