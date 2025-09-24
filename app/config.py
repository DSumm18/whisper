"""Configuration helpers for the Whisper desktop controller."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, Dict

LOGGER = logging.getLogger(__name__)

CONFIG_FILE_NAME = "config.json"


@dataclass
class Settings:
    """Strongly typed user configuration for the desktop controller."""

    hotkey: str = "ctrl+shift+space"
    mouse_button: str | None = None
    start_on_launch: bool = False
    log_file: str = "logs/whisper-ui.log"

    @classmethod
    def load(cls, path: str | Path | None = None) -> "Settings":
        """Load configuration from ``path`` or the default ``config.json``.

        Missing files fall back to the class defaults.
        """

        config_path = Path(path) if path else Path(CONFIG_FILE_NAME)
        values: Dict[str, Any] = {}
        if config_path.exists():
            try:
                with config_path.open("r", encoding="utf-8") as handle:
                    raw = json.load(handle)
            except json.JSONDecodeError as exc:  # pragma: no cover - defensive path
                LOGGER.error("Invalid JSON in %%s: %%s", config_path, exc)
                raw = {}
        else:
            LOGGER.info(
                "Configuration file %%s not found – falling back to defaults.",
                config_path,
            )
            raw = {}

        for field in fields(cls):
            if field.name in raw:
                values[field.name] = raw[field.name]

        settings = cls(**values)
        LOGGER.debug("Loaded settings: %%s", settings)
        return settings

    def ensure_log_directory(self) -> Path:
        """Create the directory that will contain the log file if needed."""

        log_path = Path(self.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        return log_path
