"""Manual verification helper for the output pipeline."""

from __future__ import annotations

import argparse
import logging
import sys
import time

from app.output import InjectionError, OutputManager


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--quick-edit",
        action="store_true",
        help="Open the overlay editor before sending text.",
    )
    parser.add_argument(
        "--text",
        default="Whisper output integration test.",
        help="Transcript to deliver to the active window.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=5.0,
        help="Seconds to wait before sending text so you can focus the editor.",
    )
    parser.add_argument(
        "--no-repeat",
        action="store_true",
        help="Skip repeating the last sentence after the initial delivery.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)

    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    manager = OutputManager()

    logging.info("You have %.1f seconds to focus the target editor...", args.delay)
    time.sleep(max(0.0, args.delay))

    try:
        delivered = manager.send_transcript(args.text, quick_edit=args.quick_edit)
    except InjectionError as exc:
        logging.error("Injection failed: %s", exc)
        return 1

    logging.info("Delivered transcript: %s", delivered)

    if not args.no_repeat:
        repeated = manager.repeat_last_sentence()
        if repeated is None:
            logging.warning("Repeat command could not run because history was empty.")
        else:
            logging.info("Repeated transcript: %s", repeated)

    return 0


if __name__ == "__main__":  # pragma: no cover - manual execution
    raise SystemExit(main())
