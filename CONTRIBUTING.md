# Contributing

Use macOS and Python 3.11. From the repository root:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest tests
```

Tests use a temporary user-data directory and Qt's offscreen platform by default. This keeps automated tests away from your saved macros and stats. Tests do not replace a manual Roblox run on the intended display setup.

## Code organization

- `macro_app_main.py` wires the app together.
- `macro_app/controllers/` owns UI behavior.
- `macro_app/services/` owns execution, detection, capture, and input logic.
- `macro_app/state.py` contains shared state.
- `macro_json.py` defines saved macros and defaults.
- `jam_detector_test.py` and `jam_detector_complete_test.py` are runtime modules despite their names.
- `dev_util/` contains manual capture and inspection utilities; these may interact with your desktop.

Keep runtime assets at their existing paths. `macros/` contains map-folder markers; user macros are saved under Application Support. No ready-made gameplay macros are bundled in the initial public version.

## Updating the UI

Edit `macro_app.ui`, then regenerate the Python module with the pinned PySide6 version:

```bash
pyside6-uic macro_app.ui -o macro_app/ui_generated.py
```

Commit both files and run the UI smoke tests. Do not hand-edit generated widget code.

## Building a macOS app

Activate the intended Python environment and run from the repository root:

```bash
pyside6-deploy -c pysidedeploy.spec
```

The spec uses relative resource paths. The deployment tool may populate local interpreter/icon paths; remove machine-specific values before committing spec changes. Preserve inclusion of `references/`, `ui_references/`, `map_images/`, `macros/`, and RapidOCR package data. Validate packaged screen capture, permissions, input, and OCR separately before releasing a build. Keep app bundles and downloads in GitHub Releases rather than Git source history.

## Changes and reports

Describe the behavior changed and the checks you ran. Include sanitized logs for bugs; omit webhook URLs, keys, and personal screenshots. Do not commit generated logs, environments, user macros, or build outputs. Report security issues privately as described in [SECURITY.md](SECURITY.md).
