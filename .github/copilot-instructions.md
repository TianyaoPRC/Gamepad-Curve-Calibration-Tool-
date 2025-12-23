# GitHub Copilot / AI Agent Instructions for stick_calibrator ⚙️

Purpose: Give an AI coding agent immediate, actionable context so it can be productive making small fixes, adding features, or preparing releases.

## Big picture
- This is a small Windows desktop tool (Tk UI) for measuring and visualizing joystick curves and emulating a virtual gamepad.  Main components:
  - `launcher.py` – entrypoint used by CLI and PyInstaller; first runs prereq checks then starts UI.
  - `ui_app.py` – single-file Tk-based UI, app state machine, hotkey handling, logging, and CSV/export logic.
  - `controllers/gamepad_vigem.py` – encapsulates `vgamepad` usage and provides a robust `VirtualGamepad` API (neutral on init, keepalive, hold behavior).
  - `detectors/` – modules with measurement/detection logic (e.g., `manual.py`, `base.py`).
  - `prereqs/` – included installer(s) (ViGEmBus) packaged into releases.
  - `stick_calibrator.spec` – PyInstaller spec: hiddenimports, datas (prereqs), and explicit handling of `ViGEmClient.dll`.

## How to run & debug locally 🔧
- Normal dev run: `python launcher.py` (this calls `ensure_prereqs_or_exit()` first).
- If you need to bypass prereqs for quick dev, import `ui_app` directly in a REPL or run `python -c "import ui_app; ui_app.main()"`.
- UI logs are written to `logs/run_log_<timestamp>.txt`. When frozen (PyInstaller) base dir is `sys._MEIPASS`/exe dir.
- The prereqs installer flow will prompt the user with Tk messageboxes and may launch the installer via UAC.

## Packaging / Release notes 🏷️
- Build with PyInstaller using the provided spec: `pyinstaller stick_calibrator.spec`.
  - Spec explicitly uses `launcher.py` as entrypoint (DO NOT change entry script without updating spec).
  - `datas` includes `prereqs/` so ViGEm installers are packaged into the EXE.
  - `hiddenimports` collects `vgamepad` and `controllers` modules and forces bundling of `ViGEmClient.dll` if present.

## Important behaviors & conventions (do not break) ⚠️
- Prereq enforcement: `prereqs_installer.ensure_prereqs_or_exit()` exits the process with SystemExit codes when prereqs missing or installer not confirmed. Tests/automation should account for this.
- Hotkeys: `ui_app` supports two hotkey backends: `keyboard_name` (friendly names like `f6`) and `keyboard_scan` (scan codes). Single-character digits/symbols force `keyboard_scan`.
  - Hotkey registration falls back automatically to scan-mode on failures (e.g., full-screen privileges/kb interception).
- Virtual gamepad: `controllers/gamepad_vigem.VirtualGamepad` handles DS4 vs Xbox mapping and always calls `neutral()` on construction or on exceptions to avoid producing stuck inputs.
- Logging: use logger `stick_calibrator` and `_log_user_hint()` for structured hint messages with `[HINT]/[CAUSE]/[ACTION]` tags.

## Files to reference for common tasks 📚
- Fix UI/state issues: `ui_app.py` (large; search for `# =================` sections to find subsystems).
- Gamepad behavior: `controllers/gamepad_vigem.py` (good examples: `set_sticks`, `neutral`, `tap_keepalive_button`, `hold_button`).
- Pre-req logic & installer UX: `prereqs_installer.py` (shows UAC launch, messagebox flows, return codes).
- Packaging hooks: `stick_calibrator.spec` (hiddenimports/datas/binaries handling is explicit and necessary for releases).

## Concrete examples for agents (do this, not vague guidance) ✅
- To add a new hidden-import for packaging a dependency used by UI: update `stick_calibrator.spec`'s `hiddenimports` using `collect_submodules('yourpackage')`.
- To add a new log hint when an operation fails, call `_log_user_hint(title, cause, action, who='BUG')` so messages are consistent.
- When modifying hotkey behavior, update `_is_symbol_or_digit_single_key()` and the place where `hotkey_backend` is `set()` (search `_auto_select_backend`).

## Missing/observed gaps worth asking about 💡
- There are no unit tests or CI configs in this repo — confirm preferred test framework and whether headless UI tests are desired.
- Confirm whether packaging should produce single-file (`--onefile`) exe or folder (`--onedir`) builds for release automation.

---

If you'd like, I can: add quick unit tests for `controllers/gamepad_vigem.py` or draft a GitHub Actions workflow to run a build and smoke test the exe. Any part of the guidance above unclear or incomplete? Please call out sections you want expanded or revised.