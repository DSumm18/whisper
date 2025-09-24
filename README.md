# whisper desktop controller

A lightweight desktop companion for Whisper-style voice typing. The tray icon
lets you toggle the transcriber service, view status, and quit the app without
opening a terminal. Hotkeys, including auxiliary mouse buttons, can be
customised to match your workflow.

## Features

- Cross-platform tray icon with start/stop/status menu items powered by
  [`pystray`](https://github.com/moses-palmer/pystray).
- Keyboard and mouse hotkey support using the [`keyboard`](https://github.com/boppreh/keyboard)
  and [`mouse`](https://github.com/boppreh/mouse) libraries.
- Visual state feedback via icon colour and tooltip text for stopped, listening,
  transcribing, and error states.
- Audible feedback cues for key lifecycle events.
- Structured logging with timestamps for troubleshooting.

## Requirements

- Python 3.9+
- Desktop environment that supports system tray icons (Windows, macOS, or most
  Linux distributions running a modern DE).
- The `keyboard` library may require administrator/root privileges on Linux and
  macOS. Consult the library documentation if hotkeys do not trigger.

Install Python dependencies with:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration

Hotkeys and runtime behaviour live in `config.json`. Copy the example file and
adjust values to suit your setup:

```bash
cp config.example.json config.json
```

Available fields:

| Field | Description | Default |
| --- | --- | --- |
| `hotkey` | Keyboard hotkey string recognised by the `keyboard` library (e.g. `ctrl+shift+space`). | `ctrl+shift+space` |
| `mouse_button` | Optional mouse button trigger. Use `x1` or `x2` for side buttons, or `left`/`right`/`middle`. Set to `null` to disable. | `null` |
| `start_on_launch` | If `true`, the transcriber begins listening as soon as the tray icon loads. | `false` |
| `log_file` | Location for the application log file. Parent directories are created automatically. | `logs/whisper-ui.log` |

The example `config.example.json` enables the first side mouse button (`x1`) and can
be edited to suit your gear. Changes take effect the next time you launch the tray
application. If no `config.json` is found the defaults above are used automatically.

## Usage

1. Activate your virtual environment if not already active.
2. Start the tray controller:

   ```bash
   python main.py
   ```

3. A tray icon appears:
   - Grey – stopped
   - Blue – listening for audio
   - Green – actively transcribing
   - Red – error state

4. Use the configured hotkey or the tray menu to start/stop the transcriber.
   State changes emit short beeps; errors use a lower tone to stand out.
5. View `logs/whisper-ui.log` for diagnostic information such as hotkey
   registration and state transitions.

Quit the application from the tray menu or by closing the terminal window used
to launch it.

## Extending the transcriber

The included `TranscriberService` is a lightweight state machine. Integrate
your audio capture and Whisper pipeline by calling:

- `begin_transcription()` before audio is sent to Whisper.
- `complete_transcription()` when Whisper returns text.
- `set_error("message")` to surface failures in the tray UI and logs.

These callbacks keep the UI responsive while your own transcription logic runs
in the background.
