# whisper

Voice typing replica of Whisper flow with output automation utilities.

## Output pipeline

The `app.output` module delivers transcripts to the currently focused
application through a combination of clipboard injection and simulated
keystrokes. The workflow is designed to:

- respect the user's focus by capturing and restoring the active window when
  possible,
- preserve Unicode content and UK spellings without auto-correcting dictated
  text,
- provide a quick-edit overlay before committing text, and
- fall back gracefully by saving the transcript to disk and copying it to the
  clipboard if automated delivery is unavailable.

### Quick correction commands

`OutputManager` exposes a handful of high-level helpers:

- `send_transcript(text, quick_edit=False)` – normalises the text, optionally
  opens the overlay editor for last-minute changes, and attempts to inject the
  result.
- `repeat_last_sentence()` – replays the most recent transcript using the same
  injection strategies.
- `open_overlay_editor(initial_text)` – open the overlay editor on demand
  without immediately sending the text.

### Optional dependencies

The module uses optional OS-specific libraries when available:

- `pywinauto` for Windows clipboard and key events,
- `AppKit` (via `pyobjc`) for macOS clipboard access, and
- `pyautogui` for cross-platform hotkeys and simulated typing.

It falls back to Tkinter-based clipboard management and emits actionable
warnings when none of the automation layers are available.

### Manual end-to-end verification

Manual scripts covering Windows, macOS, and Linux editors live in
`scripts/manual`. Run the cross-platform helper:

```bash
python scripts/manual/run_output_manual.py [--quick-edit]
```

Detailed platform checklists are documented in
[`scripts/manual/README.md`](scripts/manual/README.md).

## Tests

Automated unit tests validate text normalisation, fallback handling, history
tracking, and overlay behaviour. Execute them with:

```bash
python -m pytest
```
