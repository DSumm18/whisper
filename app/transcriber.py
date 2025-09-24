"""Simple transcriber service state machine used by the desktop UI."""

from __future__ import annotations

import enum
import logging
from threading import RLock
from typing import Callable, List

LOGGER = logging.getLogger(__name__)


class TranscriberState(enum.Enum):
    """Lifecycle state of the transcription engine."""

    STOPPED = "stopped"
    LISTENING = "listening"
    TRANSCRIBING = "transcribing"
    ERROR = "error"


StateCallback = Callable[["TranscriberState"], None]


class TranscriberService:
    """State container that mirrors a transcription engine.

    The implementation here focuses on state tracking.  Projects can plug in
    their own audio capture and Whisper integration and call ``begin_transcription``
    and ``complete_transcription`` to update the tray UI.
    """

    def __init__(self) -> None:
        self._state = TranscriberState.STOPPED
        self._callbacks: List[StateCallback] = []
        self._lock = RLock()

    @property
    def state(self) -> TranscriberState:
        with self._lock:
            return self._state

    def register_state_callback(self, callback: StateCallback) -> None:
        """Register a callback invoked whenever the state changes."""

        self._callbacks.append(callback)

    def _notify(self) -> None:
        for callback in list(self._callbacks):
            try:
                callback(self._state)
            except Exception:  # pragma: no cover - defensive logging
                LOGGER.exception("State callback failed")

    def start(self) -> None:
        """Set the service state to :class:`TranscriberState.LISTENING`."""

        with self._lock:
            if self._state == TranscriberState.LISTENING:
                LOGGER.debug("Transcriber already in listening state")
                return
            LOGGER.info("Transcriber listening started")
            self._state = TranscriberState.LISTENING
        self._notify()

    def stop(self) -> None:
        """Return the service to the :class:`TranscriberState.STOPPED` state."""

        with self._lock:
            if self._state == TranscriberState.STOPPED:
                LOGGER.debug("Transcriber already stopped")
                return
            LOGGER.info("Transcriber stopped")
            self._state = TranscriberState.STOPPED
        self._notify()

    def toggle(self) -> TranscriberState:
        """Toggle between running and stopped states."""

        with self._lock:
            if self._state in (TranscriberState.STOPPED, TranscriberState.ERROR):
                self._state = TranscriberState.LISTENING
                LOGGER.info("Transcriber listening started via toggle")
            else:
                self._state = TranscriberState.STOPPED
                LOGGER.info("Transcriber stopped via toggle")
            new_state = self._state
        self._notify()
        return new_state

    def begin_transcription(self) -> None:
        """Mark that audio is actively being transcribed."""

        with self._lock:
            LOGGER.info("Transcription started")
            self._state = TranscriberState.TRANSCRIBING
        self._notify()

    def complete_transcription(self) -> None:
        """Return to the listening state once transcription finished."""

        with self._lock:
            LOGGER.info("Transcription finished")
            self._state = TranscriberState.LISTENING
        self._notify()

    def set_error(self, message: str) -> None:
        """Set the state to :class:`TranscriberState.ERROR` with log context."""

        with self._lock:
            LOGGER.error("Transcriber error: %s", message)
            self._state = TranscriberState.ERROR
        self._notify()
