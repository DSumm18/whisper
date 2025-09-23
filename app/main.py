"""Entry point for launching the Whisper Flow desktop assistant."""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .config import DEFAULT_CONFIG_PATH, load_config, save_config
from .ui import VoiceTypingApp


_LOGGER = logging.getLogger("whisper-flow")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to the YAML configuration file.",
    )
    parser.add_argument(
        "--create-config",
        action="store_true",
        help="Write the current defaults to the configuration file and exit.",
    )
    parser.add_argument(
        "--no-tray",
        action="store_true",
        help="Run without a system tray icon (useful for headless testing).",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Verbosity of logging output.",
    )
    return parser.parse_args()


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main() -> None:
    args = parse_args()
    configure_logging(args.log_level)
    config = load_config(args.config)
    if args.create_config:
        save_config(config, args.config)
        _LOGGER.info("Wrote configuration to %s", args.config)
        return
    if args.no_tray:
        app = VoiceTypingApp(config)
        app._icon = None  # force CLI mode
        app.run()
        return
    app = VoiceTypingApp(config)
    app.run()


if __name__ == "__main__":  # pragma: no cover
    main()
