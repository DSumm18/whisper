# Whisper Flow Desktop Assistant

A cross-platform voice typing companion inspired by WhisperFlow. The app wraps
OpenAI's Whisper models in a friendly desktop experience so you can dictate UK
English text anywhere on your machine with a single hotkey.

## Features

- 🎙️ **Always-on listening** – start and stop dictation from the system tray or a
global hotkey.
- 🧠 **Whisper-based transcription** – stream audio from your microphone to an
open-source Whisper model tuned for British spelling.
- 🪟 **Works in any app** – inject recognised text into the focused window using
the clipboard or simulated typing.
- 🔁 **Quick retry** – instantly re-run the last transcription if Whisper misheard
you.
- 🖱️ **Mouse & keyboard triggers** – bind side buttons or keyboard combos for
toggle/push-to-talk control.
- 🔔 **Notifications** – optional desktop pop-ups confirm what was typed.
- ⚙️ **Customisable YAML config** – tweak audio sensitivity, Whisper parameters,
output behaviour and more.

## Getting Started

### 1. Install dependencies

Create a virtual environment and install the package with the `full` extra to
pull in audio, UI and hotkey dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -e .[full]
```

> ℹ️ Installing Whisper downloads the selected model on first run. Use the
> `model_size` option in `config.yaml` to pick `tiny`, `base`, `small`, etc.

### 2. Launch the assistant

```bash
python -m app.main
```

The first launch creates a `config.yaml` with sensible defaults. The app places
a tray icon (if supported on your OS) and starts listening when you hit the
default hotkey `Ctrl+Alt+Space`.

Use `python -m app.main --no-tray` to run purely in the terminal – handy for
minimal window managers or SSH sessions.

### 3. Dictate into any application

1. Focus the app where you want text (browser, email, IDE, …).
2. Press the toggle hotkey or click “Start listening” from the tray.
3. Speak naturally. Whisper sends the transcript as soon as it detects a pause.
4. Press the hotkey again or use the tray to stop listening.

The assistant copies the text to your clipboard, pastes it into the active
window and optionally restores your previous clipboard contents.

## Configuration

All settings live in `config.yaml`. Important options include:

```yaml
audio:
  sample_rate: 16000
  block_size: 2048
  min_duration: 1.2
  silence_duration: 0.7
  silence_threshold: 0.015
transcription:
  model_size: base
  language: en
  temperature: 0.0
  beam_size: 5
hotkey:
  toggle_key: ctrl+alt+space
  push_to_talk: null
  mouse_button: xbutton1
output:
  method: clipboard
  restore_clipboard: true
  auto_capitalise: true
  auto_punctuation: true
ui:
  show_notifications: true
```

Adjust the hotkeys to suit your keyboard layout or change `mouse_button` to a
side button on gaming mice. Set `output.method` to `type` if you prefer the app
to “type” characters instead of pasting.

Run `python -m app.main --create-config` to rewrite the configuration file with
the current defaults.

## Development

Run the automated tests with:

```bash
python -m pytest
```

The tests use deterministic audio fixtures to verify buffering, retry logic and
config persistence without relying on microphone hardware.

## Roadmap

- Lightweight overlay editor for quick corrections before inserting text.
- Optional wake word detection to go hands-free.
- Packaging for Windows/macOS/Linux installers.

PRs and feature ideas are very welcome. Happy dictating!
