# Repository Guidelines

## Project Structure & Module Organization

- `main.py` contains `DrawingBoardApp`, menus, the custom Help window, pencil/rubber event handlers, color selection, undo, and Pillow image import/export logic. Its entry point starts the desktop application.
- `eraser.py` contains the pure `remaining_segments` geometry helper for continuous rubber drags; keep this module independent of Tkinter.
- `logo.py` renders the geometric application logo with Pillow. The app uses it at runtime; `media/logo.png` is the README version.
- `tests/test_main.py` covers application behavior with mocked Tk widgets. `tests/test_eraser.py` covers real geometry and rubber behavior using a stateful canvas mock; `tests/__init__.py` enables test discovery.
- `media/` holds the logo, screenshots, and demo assets used by `README.md`. Older demos may not show the current controls.
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

Cover click-only dots, stationary motion, normal drags, shared size limits, switching tools, color-picker cancellation, and theme changes. Rubber tests should cover clicks, fast and diagonal drags, partial segment cuts, dots, image preservation, and repeated erasing/undo. Check that export hides all cursor decorations and restores them after success or failure. Verify affected menu shortcuts, cursor icons, Help layout, and native dialogs in the running app.

## Drawing Tool and UI Invariants

- `File → Undo All` (`Ctrl+Shift+Z`) always asks “Are You sure you want to undo all design?” with OK/Cancel and Cancel as the default. Confirmation clears pencil marks and rubber history while preserving imported images, their image references and undo order, cursor decorations, and tool/theme settings. Individual image imports remain undoable with Ctrl+Z. Cancel preserves the design. Stop active strokes without creating a dot before opening the dialog. Cover these behaviors, repeated image-only calls, and the menu, shortcut, and Help text in tests.

- The menus are `File`, `Select`, `View`, and `Help`. `Select` offers Color (`Ctrl+Shift+C`), Pencil (`Ctrl+Shift+P`), and Rubber (`Ctrl+Shift+R`). Keep bindings, menu accelerators, Help, and README consistent.
- `pencil_size` is the shared size for both tools, initially `MIN_PENCIL_SIZE` (1 pixel), bounded by `MAX_PENCIL_SIZE` (50 pixels). `Ctrl++` / `Ctrl+-` adjust it by 1; `Ctrl+=` and numeric keypad add/subtract also work. Switching tools preserves size and pencil color.
- Default pencil marks use the `theme_color` canvas tag and follow the canvas theme: black on white, white on black. Explicit color selections, including black or white, remain fixed across theme changes. A canceled picker must preserve the selection and default/custom status.
- A click-release without motion creates a filled oval tagged `pencil_dot`. Drags create round-ended line segments. Internal calls to `stop_drawing()` must not commit a dot. Rubber hit testing must distinguish pencil dots from cursor ovals.
- Rubber erases pencil marks without painting background-colored strokes or altering imported images. Line cuts use the capsule swept between mouse events; touched dots are removed as whole marks.
- `items` is an undo history containing canvas IDs and rubber action dictionaries. Each rubber action stores an `erased` list of `(original_id, replacement_ids)` pairs. Originals remain hidden to preserve geometry and stacking; undo reverses these pairs, deletes replacements, and reveals originals. Preserve this ordering and theme tags on replacements.
- The pencil outline and rubber icon/sleeve are cursor decorations, not drawing history. Hide them on leave and during export, restore the active preview afterward, and keep them above artwork.
- Help is a reusable `Toplevel` with indented sections, bold commands, the app logo, and no standard information icon. Close, Escape, and Enter dismiss it and return focus to the canvas. Keep font, logo, and imported-image references alive.

## Commit & Pull Request Guidelines

Existing history uses date-based subjects and generic messages such as `Second commit`; no consistent convention is established. Use concise imperative subjects describing the change, such as `Fix save error cleanup`. Keep commits focused. Pull requests should explain behavior changes, report validation commands and results, link relevant issues when available, and include screenshots for visible interface changes. Update setup documentation when commands or dependencies change.
