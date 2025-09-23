# Manual output verification

These guided scenarios exercise the `app.output` module against common editors on
Windows, macOS, and Linux. Run them whenever you need to manually confirm end to
end clipboard/typing integration on a workstation with GUI access.

## Common preparation

1. Install the optional dependencies for your platform (they are all optional
   at runtime but make verification easier):

   ```bash
   pip install pyautogui
   pip install pywinauto        # Windows only
   pip install pyobjc-framework-AppKit  # macOS only
   ```

2. Ensure the voice-typing environment is in focus and that you can switch to
   a text editor quickly. The scripts assume that the editor is already open and
   ready to receive text.

3. From the repository root run:

   ```bash
   python scripts/manual/run_output_manual.py
   ```

   The script waits a few seconds so you can focus the target editor before it
   attempts clipboard or keystroke injection.

## Windows (Notepad / WordPad)

1. Open Notepad or WordPad and make sure the text caret is visible.
2. Run the manual script as described above.
3. When prompted, bring the editor to the foreground.
4. Confirm that the sentence “Whisper output integration test.” appears. If it
   does not, check that `pywinauto` and `pyautogui` are installed and that the
   script has permission to control the keyboard.
5. Trigger the quick edit scenario by running the script with `--quick-edit` and
   validate that the Tkinter overlay appears and that the edited text is
   committed to Notepad.

## macOS (TextEdit)

1. Launch TextEdit and open a plain-text document.
2. Run the manual script and follow the on-screen countdown to switch focus to
   TextEdit.
3. Verify that the default sentence appears, keeping all accent marks intact.
4. Run the script with `--quick-edit` to launch the overlay editor, adjust the
   text, and ensure the updated copy is pasted into TextEdit.

## Linux (Gedit / VS Code / LibreOffice Writer)

1. Open one of the listed editors with a blank document.
2. Execute the manual script. The script will attempt a clipboard paste and
   fall back to simulated typing if the clipboard integration is unavailable.
3. Confirm that the sentence is inserted; try again with `--quick-edit` to test
   the overlay editor.
4. If injection fails entirely, the script prints the path to a fallback file
   that contains the transcript so you can copy it manually.

Each scenario ends by repeating the last sentence using the quick correction
command to verify that history tracking works as expected.
