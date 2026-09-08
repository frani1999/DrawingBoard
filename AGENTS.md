# Repository Guidelines

## Project Structure & Module Organization

- `main.py` contains `DrawingBoardApp`, the Tkinter interface, event handlers, and Pillow image import/export logic. Its entry point starts the desktop application.
- `tests/test_main.py` contains unit tests; `tests/__init__.py` enables test discovery.
- `media/` holds screenshots and demo assets used by `README.md`.
- `doc/` contains project documentation, including `doc/SETUP.md` for platform setup and troubleshooting.
- `requirements.txt` declares dependencies, and `Makefile` provides development shortcuts.
- `.venv/` is the local Python environment and is excluded from Git.

## Build, Test, and Development Commands

Use Python 3.10 or newer. Run commands from the repository root:

- `make setup`: create `.venv` and install dependencies.
- `make create-env`: create the environment only.
- `make install`: install dependencies into an existing environment.
- `make run`: launch DrawingBoard; a graphical desktop is required.
- `make test`: run `unittest` discovery with verbose output.

There is no separate build step. GNU Make is optional. In Windows PowerShell, use `.\.venv\Scripts\python.exe main.py` to run and `.\.venv\Scripts\python.exe -m unittest discover -v` to test after setup. On macOS/Linux, use `.venv/bin/python`. See `doc/SETUP.md` for installation commands.

## Coding Style & Naming Conventions

Use four-space indentation and follow PEP 8 conventions: `snake_case` for functions and variables, `PascalCase` for classes, and `UPPER_SNAKE_CASE` for constants. Keep Tkinter callbacks compatible with optional event arguments where appropriate. Preserve canvas item tracking for undo and image references that prevent Tk images from disappearing. No formatter or linter is currently configured; follow surrounding style and avoid unrelated formatting changes.

## Testing Guidelines

Use standard-library `unittest` and `unittest.mock`. Name files `test_*.py` and methods `test_<behavior>`. Mock Tk widgets, dialogs, and external I/O so tests run without windows or Ghostscript; use real Pillow images when testing resizing. Add regression tests for fixes and cover cancellation, failure, and cleanup paths. No numeric coverage threshold is configured. Run the full suite before submitting changes; manually check affected GUI behavior because mocks do not validate rendering or actual PostScript conversion.

## Commit & Pull Request Guidelines

Existing history uses date-based subjects and generic messages such as `Second commit`; no consistent convention is established. Use concise imperative subjects describing the change, such as `Fix save error cleanup`. Keep commits focused. Pull requests should explain behavior changes, report validation commands and results, link relevant issues when available, and include screenshots for visible interface changes. Update setup documentation when commands or dependencies change.
