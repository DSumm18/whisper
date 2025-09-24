"""Entry point for the Whisper desktop tray controller."""

from __future__ import annotations

import logging

from app import Settings, TrayApplication, TranscriberService


def configure_logging(settings: Settings) -> None:
    log_path = settings.ensure_log_directory()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def main() -> None:
    settings = Settings.load()
    configure_logging(settings)

    service = TranscriberService()
    tray = TrayApplication(service, settings)

    tray.run()


if __name__ == "__main__":  # pragma: no cover - script entry point
    main()
