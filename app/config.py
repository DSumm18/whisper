"""Configuration management for the Whisper desktop assistant.

This module provides data classes that capture the configuration options for
running the application as well as helpers for loading and persisting the
configuration to YAML files.  The defaults are tuned for UK English dictation
with the open source Whisper models.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, Optional

try:  # pragma: no cover - optional dependency
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore


DEFAULT_CONFIG_PATH = Path("config.yaml")


@dataclass
class AudioConfig:
    """Configuration for microphone capture and voice activity detection."""

    sample_rate: int = 16_000
    block_size: int = 2_048
    min_duration: float = 1.2  # seconds of speech before transcribing
    silence_duration: float = 0.7  # silence required to finish a segment
    silence_threshold: float = 0.015  # amplitude threshold that counts as silence
    input_device: Optional[int] = None


@dataclass
class TranscriptionConfig:
    """Parameters controlling Whisper model behaviour."""

    model_size: str = "base"
    language: str = "en"
    temperature: float = 0.0
    beam_size: int = 5
    best_of: int = 5
    condition_on_previous_text: bool = False
    initial_prompt: Optional[str] = (
        "You are dictating UK English text. Prefer British spelling conventions."
    )


@dataclass
class HotkeyConfig:
    """Settings for the global hotkey bindings."""

    toggle_key: str = "ctrl+alt+space"
    push_to_talk: Optional[str] = None
    mouse_button: Optional[str] = "xbutton1"


@dataclass
class OutputConfig:
    """Configuration for how recognised text is injected into the OS."""

    method: str = "clipboard"
    restore_clipboard: bool = True
    auto_capitalise: bool = True
    auto_punctuation: bool = True
    fallback_notification: bool = True


@dataclass
class UiConfig:
    """Visual behaviour of the tray UI."""

    start_minimised: bool = True
    show_notifications: bool = True


@dataclass
class AppConfig:
    """Top level configuration container."""

    audio: AudioConfig = field(default_factory=AudioConfig)
    transcription: TranscriptionConfig = field(default_factory=TranscriptionConfig)
    hotkey: HotkeyConfig = field(default_factory=HotkeyConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    ui: UiConfig = field(default_factory=UiConfig)

    @staticmethod
    def default() -> "AppConfig":
        """Return a configuration with all default values."""

        return AppConfig()

    def to_dict(self) -> Dict[str, Any]:
        """Serialise the configuration to a dict suitable for YAML output."""

        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "AppConfig":
        """Create a configuration object from a dictionary."""

        def build(cls, key: str):
            section = data.get(key, {})
            return cls(**section) if isinstance(section, dict) else cls()

        return AppConfig(
            audio=build(AudioConfig, "audio"),
            transcription=build(TranscriptionConfig, "transcription"),
            hotkey=build(HotkeyConfig, "hotkey"),
            output=build(OutputConfig, "output"),
            ui=build(UiConfig, "ui"),
        )


def load_config(path: Path | str = DEFAULT_CONFIG_PATH) -> AppConfig:
    """Load configuration from *path* or create defaults when missing."""

    path = Path(path)
    if not path.exists():
        config = AppConfig.default()
        save_config(config, path)
        return config

    with path.open("r", encoding="utf8") as handle:
        data = _load_serialised(handle)
    return AppConfig.from_dict(data)


def save_config(config: AppConfig, path: Path | str = DEFAULT_CONFIG_PATH) -> None:
    """Persist *config* to disk as YAML."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf8") as handle:
        _dump_serialised(config.to_dict(), handle)


def _load_serialised(handle) -> Dict[str, Any]:
    if yaml is not None:  # pragma: no branch - simple import guard
        data = yaml.safe_load(handle) or {}
        if isinstance(data, dict):
            return data
        return {}
    import json

    try:
        data = json.load(handle)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _dump_serialised(data: Dict[str, Any], handle) -> None:
    if yaml is not None:  # pragma: no branch
        yaml.safe_dump(data, handle, sort_keys=False)
        return
    import json

    json.dump(data, handle, indent=2)


__all__ = [
    "AudioConfig",
    "TranscriptionConfig",
    "HotkeyConfig",
    "OutputConfig",
    "UiConfig",
    "AppConfig",
    "load_config",
    "save_config",
    "DEFAULT_CONFIG_PATH",
]
