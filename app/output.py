"""Utilities for delivering transcripts to the active application.

This module coordinates clipboard injection, simulated keystrokes, and
light-weight correction helpers so that speech-to-text transcripts can be
committed to the currently focused application in a controlled way.  The
implementation is intentionally defensive: it attempts platform-specific
integration using optional dependencies and falls back to safe no-op behaviour
when those dependencies are unavailable (for example inside headless test
runs).
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
import logging
import os
import platform
from pathlib import Path
from typing import Callable, Deque, Optional, Sequence
import unicodedata

logger = logging.getLogger(__name__)


class InjectionError(RuntimeError):
    """Raised when text cannot be injected into the active application."""


def normalise_transcript(text: str) -> str:
    """Return a normalised representation of *text*.

    The routine keeps the words as dictated (including UK spelling such as
    "colour" or "organisation") while ensuring we have a consistent Unicode
    normalisation form and that surrounding whitespace is tidy.  Leading and
    trailing whitespace is trimmed, but internal line breaks are preserved.
    """

    if text is None:
        raise TypeError("text cannot be None")

    if not isinstance(text, str):
        text = str(text)

    normalised = unicodedata.normalize("NFC", text)
    normalised = normalised.replace("\r\n", "\n").replace("\r", "\n")
    normalised = "\n".join(line.rstrip() for line in normalised.split("\n"))
    return normalised.strip()


def _import_pyautogui():
    try:
        import pyautogui  # type: ignore

        # Disable failsafe so we do not interrupt automation if the cursor hits
        # the corner while typing; users can still enable it explicitly.
        try:
            pyautogui.FAILSAFE = False
        except Exception:  # pragma: no cover - depends on pyautogui internals
            pass
        return pyautogui
    except Exception as exc:  # pragma: no cover - executed only when missing
        logger.debug("pyautogui unavailable: %s", exc)
        return None


def _import_pywinauto_clipboard():
    try:
        from pywinauto import clipboard  # type: ignore

        return clipboard
    except Exception as exc:  # pragma: no cover - optional dependency
        logger.debug("pywinauto clipboard unavailable: %s", exc)
        return None


def _import_pywinauto_sendkeys():
    try:
        from pywinauto.keyboard import SendKeys  # type: ignore

        return SendKeys
    except Exception as exc:  # pragma: no cover - optional dependency
        logger.debug("pywinauto SendKeys unavailable: %s", exc)
        return None


def _import_appkit_pasteboard():
    try:
        from AppKit import NSPasteboard, NSStringPboardType  # type: ignore

        return NSPasteboard.generalPasteboard, NSStringPboardType
    except Exception as exc:  # pragma: no cover - optional dependency
        logger.debug("AppKit pasteboard unavailable: %s", exc)
        return None


def _copy_to_clipboard(text: str) -> bool:
    system = platform.system()
    if system == "Windows":
        clipboard = _import_pywinauto_clipboard()
        if clipboard is not None:
            try:
                clipboard.copy(text)
                return True
            except Exception as exc:  # pragma: no cover - external dependency
                logger.debug("pywinauto clipboard copy failed: %s", exc)

    if system == "Darwin":
        pasteboard_info = _import_appkit_pasteboard()
        if pasteboard_info is not None:
            general_pasteboard, string_type = pasteboard_info
            try:  # pragma: no cover - requires macOS runtime
                board = general_pasteboard()
                board.clearContents()
                board.setString_forType_(text, string_type)
                return True
            except Exception as exc:
                logger.debug("AppKit pasteboard copy failed: %s", exc)

    # Cross-platform tkinter clipboard fallback.
    try:
        import tkinter as tk  # type: ignore

        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()
        root.destroy()
        return True
    except Exception as exc:  # pragma: no cover - depends on GUI availability
        logger.debug("tkinter clipboard copy failed: %s", exc)

    return False


def _paste_from_clipboard(system: str) -> bool:
    pyautogui = _import_pyautogui()

    if system == "Windows":
        sendkeys = _import_pywinauto_sendkeys()
        if sendkeys is not None:
            try:
                sendkeys("^v")
                return True
            except Exception as exc:  # pragma: no cover - external dependency
                logger.debug("pywinauto SendKeys failed: %s", exc)

    if pyautogui is not None:
        try:
            if system == "Darwin":
                pyautogui.hotkey("command", "v")
            else:
                pyautogui.hotkey("ctrl", "v")
            return True
        except Exception as exc:  # pragma: no cover - runtime specific
            logger.debug("pyautogui hotkey failed: %s", exc)
            if system not in {"Darwin"}:
                try:
                    pyautogui.hotkey("ctrl", "shift", "v")
                    return True
                except Exception as exc2:  # pragma: no cover
                    logger.debug("pyautogui ctrl+shift+v failed: %s", exc2)

    return False


def _type_via_pyautogui(text: str, interval: float = 0.01) -> bool:
    pyautogui = _import_pyautogui()
    if pyautogui is None:
        return False

    try:
        pyautogui.typewrite(text, interval=interval)
        return True
    except Exception as exc:  # pragma: no cover - runtime specific
        logger.debug("pyautogui typewrite failed: %s", exc)
        return False


class ClipboardInjector:
    """Inject text by copying to the clipboard then pasting it."""

    def __call__(self, text: str) -> None:
        prepared = normalise_transcript(text)
        if not _copy_to_clipboard(prepared):
            raise InjectionError("Unable to copy transcript to clipboard")

        system = platform.system()
        if not _paste_from_clipboard(system):
            raise InjectionError("Unable to paste transcript via clipboard")


class KeystrokeInjector:
    """Inject text via simulated keystrokes."""

    def __init__(self, interval: float = 0.01) -> None:
        self.interval = interval

    def __call__(self, text: str) -> None:
        prepared = normalise_transcript(text)
        if not _type_via_pyautogui(prepared, interval=self.interval):
            raise InjectionError("Unable to type transcript via simulated keys")


def default_injectors() -> Sequence[Callable[[str], None]]:
    return (ClipboardInjector(), KeystrokeInjector())


class FocusManager:
    """Tracks and restores the application that was focused before output."""

    def __init__(self, pyautogui_module=None) -> None:
        self._pyautogui = pyautogui_module if pyautogui_module is not None else _import_pyautogui()
        self._last_window = None

    def capture(self) -> Optional[object]:
        if self._pyautogui is None:
            return None
        get_window = getattr(self._pyautogui, "getActiveWindow", None)
        if not callable(get_window):
            return None
        try:
            self._last_window = get_window()
        except Exception as exc:  # pragma: no cover - depends on runtime
            logger.debug("Failed to capture active window: %s", exc)
            self._last_window = None
        return self._last_window

    def restore(self) -> bool:
        if self._last_window is None:
            return False
        activate = getattr(self._last_window, "activate", None)
        if not callable(activate):
            return False
        try:
            activate()
            return True
        except Exception as exc:  # pragma: no cover - depends on runtime
            logger.debug("Failed to restore window focus: %s", exc)
            return False


def _fallback_path() -> Path:
    env_path = os.getenv("WHISPER_OUTPUT_FALLBACK_PATH")
    if env_path:
        return Path(env_path).expanduser()

    cache_home = Path(os.getenv("XDG_CACHE_HOME", Path.home() / ".cache"))
    return cache_home / "whisper" / "last_transcript.txt"


def default_fallback_handler(text: str) -> Path:
    """Persist the transcript so that the user can paste it manually later."""

    fallback_file = _fallback_path()
    fallback_file.parent.mkdir(parents=True, exist_ok=True)
    fallback_file.write_text(text, encoding="utf-8")

    if _copy_to_clipboard(text):
        logger.warning(
            "Automatic injection failed. The transcript was copied to the "
            "clipboard and saved to %s.",
            fallback_file,
        )
    else:
        logger.warning(
            "Automatic injection failed. The transcript is stored at %s.",
            fallback_file,
        )
    return fallback_file


def default_overlay_editor(initial_text: str, *, focus_manager: Optional[FocusManager] = None) -> str:
    """Open a very small Tkinter overlay for last-minute corrections.

    The editor is optional; if Tkinter is not available (for example in
    headless CI) the function simply returns ``initial_text`` unchanged.  When
    the editor is shown the previous application focus is restored afterwards.
    """

    try:
        import tkinter as tk  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dependency
        logger.debug("tkinter unavailable for overlay editor: %s", exc)
        return initial_text

    if focus_manager is not None:
        focus_manager.capture()

    result: dict[str, str] = {"text": initial_text}
    finished = False

    def on_confirm() -> None:
        nonlocal finished
        result["text"] = text_widget.get("1.0", "end-1c")
        finished = True
        root.destroy()

    def on_cancel() -> None:
        nonlocal finished
        finished = True
        root.destroy()

    root = tk.Tk()
    root.title("Quick transcript edit")
    root.attributes("-topmost", True)
    root.geometry("400x200")

    text_widget = tk.Text(root, wrap="word")
    text_widget.insert("1.0", initial_text)
    text_widget.pack(expand=True, fill="both")

    button_frame = tk.Frame(root)
    button_frame.pack(fill="x", pady=4)
    tk.Button(button_frame, text="Send", command=on_confirm).pack(side="left", expand=True)
    tk.Button(button_frame, text="Cancel", command=on_cancel).pack(side="right", expand=True)

    text_widget.focus_force()
    root.mainloop()

    if focus_manager is not None:
        focus_manager.restore()

    if not finished:
        # The user closed the window via OS controls.
        return initial_text

    return normalise_transcript(result["text"])


@dataclass
class OutputManager:
    """Manage transcript delivery and lightweight correction commands."""

    injectors_factory: Optional[Callable[[], Sequence[Callable[[str], None]]]] = None
    overlay_editor: Optional[Callable[[str], str]] = None
    fallback_handler: Optional[Callable[[str], Path]] = None
    focus_manager: FocusManager = field(default_factory=FocusManager)
    history_limit: int = 50

    def __post_init__(self) -> None:
        if self.injectors_factory is None:
            self._injectors = list(default_injectors())
        else:
            self._injectors = list(self.injectors_factory())

        if self.overlay_editor is None:
            self.overlay_editor = lambda text: default_overlay_editor(text, focus_manager=self.focus_manager)

        if self.fallback_handler is None:
            self.fallback_handler = default_fallback_handler

        self._history: Deque[str] = deque(maxlen=self.history_limit)

    @property
    def history(self) -> Sequence[str]:
        return tuple(self._history)

    def send_transcript(self, text: str, *, quick_edit: bool = False) -> str:
        """Deliver *text* to the active application.

        When ``quick_edit`` is true the overlay editor is opened to allow the
        user to polish the text before injection.  The method records the final
        text in a bounded history so it can be repeated quickly.
        """

        prepared = normalise_transcript(text)

        if quick_edit and self.overlay_editor is not None:
            try:
                prepared = self.overlay_editor(prepared)
            except Exception as exc:
                logger.warning("Overlay editor failed: %s", exc)

        delivered = False
        last_error: Optional[Exception] = None
        for injector in self._injectors:
            try:
                injector(prepared)
            except InjectionError as exc:
                logger.debug("Injector %s failed: %s", injector, exc)
                last_error = exc
            except Exception as exc:  # pragma: no cover - defensive programming
                logger.exception("Unexpected error from injector %s", injector)
                last_error = exc
            else:
                delivered = True
                break

        self._history.append(prepared)

        if not delivered:
            try:
                self.fallback_handler(prepared)
            except Exception as exc:  # pragma: no cover - filesystem issues
                logger.error("Fallback handler failed: %s", exc)
                if last_error is not None:
                    raise last_error
                raise InjectionError("No injector succeeded and fallback failed") from exc
        return prepared

    def repeat_last_sentence(self) -> Optional[str]:
        """Re-inject the most recent transcript."""

        if not self._history:
            return None

        last_text = self._history[-1]
        for injector in self._injectors:
            try:
                injector(last_text)
                break
            except InjectionError as exc:
                logger.debug("Injector %s failed during repeat: %s", injector, exc)
                continue
        else:
            self.fallback_handler(last_text)
        self._history.append(last_text)
        return last_text

    def open_overlay_editor(self, initial_text: str) -> str:
        if self.overlay_editor is None:
            return normalise_transcript(initial_text)
        return self.overlay_editor(normalise_transcript(initial_text))
