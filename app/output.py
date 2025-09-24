"""Utilities for persisting generated transcripts to disk and the clipboard."""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)

ClipboardCopier = Optional[Callable[[str], bool]]


def copy_to_clipboard(text: str) -> bool:
    """Attempt to copy *text* to the system clipboard.

    The implementation relies on :mod:`pyperclip` when it is available.  The
    function returns ``True`` when the copy succeeds and ``False`` otherwise.
    Exceptions raised by the clipboard backend are caught and logged so the
    caller can continue with secondary fallbacks.
    """

    try:
        import pyperclip  # type: ignore
    except ImportError:
        logger.debug("pyperclip is not installed; clipboard copy skipped.")
        return False

    try:
        pyperclip.copy(text)
    except Exception as exc:  # pragma: no cover - backend specific exceptions
        logger.warning("Failed to copy transcript to clipboard: %s", exc)
        return False
    return True


def default_fallback_handler(
    transcript: str,
    fallback_path: Path,
    *,
    clipboard_copier: ClipboardCopier = copy_to_clipboard,
    logger: Optional[logging.Logger] = None,
) -> Optional[Path]:
    """Persist *transcript* when the primary destination is unavailable.

    The handler first tries to create the directory for ``fallback_path`` and
    write the transcript there.  When those operations raise
    :class:`OSError`/:class:`PermissionError` the handler falls back to a
    guaranteed writable directory provided by :func:`tempfile.gettempdir`.

    Regardless of where the transcript ultimately lands the handler still
    attempts to copy it to the clipboard when a ``clipboard_copier`` is
    supplied.  Any failure to both persist to disk *and* copy to the clipboard
    is surfaced through a clear warning so that callers are aware of the data
    loss.
    """

    active_logger = logger or logging.getLogger(__name__)

    disk_success = False
    clipboard_success = False
    clipboard_exc: Optional[Exception] = None

    final_path: Optional[Path] = fallback_path
    alt_path = Path(tempfile.gettempdir()) / fallback_path.name

    try:
        fallback_path.parent.mkdir(parents=True, exist_ok=True)
        fallback_path.write_text(transcript, encoding="utf-8")
        disk_success = True
    except (OSError, PermissionError) as exc:
        try:
            alt_path.parent.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError):
            # The directory from ``gettempdir`` should already exist; if it
            # does not we let the subsequent write raise and handle it below.
            pass

        try:
            alt_path.write_text(transcript, encoding="utf-8")
            final_path = alt_path
            disk_success = True
            active_logger.warning(
                "Unable to write transcript to %s (%s). Wrote to fallback location %s.",
                fallback_path,
                exc,
                alt_path,
            )
        except (OSError, PermissionError) as fallback_exc:
            final_path = None
            active_logger.warning(
                "Unable to write transcript to %s (%s) or fallback location %s (%s).",
                fallback_path,
                exc,
                alt_path,
                fallback_exc,
            )

    if clipboard_copier is not None:
        try:
            clipboard_success = bool(clipboard_copier(transcript))
        except Exception as exc:  # pragma: no cover - defensive logging
            clipboard_exc = exc
            clipboard_success = False

    if disk_success:
        if clipboard_copier is not None and not clipboard_success:
            message = "Transcript stored at %s but failed to copy to clipboard"
            if clipboard_exc is not None:
                message += f" ({clipboard_exc})"
            active_logger.warning(message + ".", final_path or fallback_path)
    else:
        if clipboard_success:
            active_logger.warning(
                "Transcript copied to clipboard because it could not be written to disk."
            )
        else:
            message = "Failed to store transcript on disk and copy it to the clipboard"
            if clipboard_exc is not None:
                message += f" ({clipboard_exc})"
            active_logger.warning(message + ".")

    return final_path if disk_success else (final_path if clipboard_success else None)


def send_transcript(
    transcript: str,
    output_path: Path | str,
    *,
    clipboard_copier: ClipboardCopier = copy_to_clipboard,
    fallback_handler: Callable[..., Optional[Path]] = default_fallback_handler,
    logger: Optional[logging.Logger] = None,
) -> Optional[Path]:
    """Write *transcript* to ``output_path``.

    When writing the transcript fails due to permission issues the provided
    ``fallback_handler`` is invoked so that the caller still receives a usable
    location (or ``None`` when recovery is impossible).
    """

    active_logger = logger or logging.getLogger(__name__)
    destination = Path(output_path)

    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(transcript, encoding="utf-8")
        return destination
    except (OSError, PermissionError) as exc:
        active_logger.warning("Failed to write transcript to %s: %s", destination, exc)
        if fallback_handler is None:
            raise
        return fallback_handler(
            transcript,
            destination,
            clipboard_copier=clipboard_copier,
            logger=active_logger,
        )
