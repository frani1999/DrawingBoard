# Set up and run DrawingBoard

DrawingBoard is a Python desktop application. Download and extract the repository
(or clone it), then open a terminal in the folder containing `main.py` and
`requirements.txt`. All commands below run from that folder.

## Prerequisites

- Python 3.10 or newer, with `pip`, `venv`, and Tkinter available. Python 3.10 was
  used to launch the app locally.
- A graphical desktop session to display the drawing window.
- Internet access for the initial dependency installation.
- Optional: GNU Make for the shortcuts below. Make is not included with Windows;
  the manual commands work without it.

On Windows, install Python with the Python launcher (`py`). On macOS or Linux,
the commands below use `python3`. If your installation uses another command,
substitute that command when creating the environment.

## Quick setup with Make

If GNU Make is installed:

```sh
make setup
make run
```

`make setup` creates `.venv` and installs the packages in `requirements.txt`.
`make run` opens the Drawing Board window. Close the window to stop the app.
On subsequent runs, only `make run` is needed.

| Command | Purpose |
| --- | --- |
| `make help` | List available commands. |
| `make create-env` | Create the local `.venv` environment. |
| `make install` | Install dependencies after creating the environment. |
| `make setup` | Create the environment and install dependencies in order. |
| `make run` | Start the application using `.venv`. |
| `make test` | Discover and run Python `unittest` tests using `.venv`. |

The Makefile selects `py` on Windows and `python3` on macOS/Linux. You can
override this when setting up, for example: `make setup PYTHON=python3.10`.

## Manual setup on Windows (PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

To start the app again later:

```powershell
.\.venv\Scripts\python.exe main.py
```

## Manual setup on macOS or Linux

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python main.py
```

To start the app again later:

```sh
.venv/bin/python main.py
```

These commands use the environment's Python directly, so activating the
environment is unnecessary. `.venv` is already excluded from Git.

## Running tests

After setup, if GNU Make is installed, run:

```sh
make test
```

If GNU Make is not installed, run the equivalent command directly:

```powershell
# Windows
.\.venv\Scripts\python.exe -m unittest discover -v
```

```sh
# macOS / Linux
.venv/bin/python -m unittest discover -v
```

The suite in `tests/test_main.py` covers drawing, undo, theme switching, image
import and resizing, canceled dialogs, and save success/failure cleanup.
It uses Python's built-in `unittest` and `unittest.mock`; no additional test
dependencies are required. Tk widgets, dialogs, and file access are mocked,
so tests do not open windows, write drawings, or require Ghostscript. Image
resizing uses real Pillow images. These unit tests do not verify the live GUI
or actual PostScript conversion.

To run one test on Windows:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_main.DrawingBoardTests.test_undo_empty_board_is_safe -v
```

Add new tests in files named `test_*.py` under `tests/` so discovery finds them.

## Troubleshooting

- **`make` is not recognized:** use the manual setup commands above.
- **`py` or `python3` is not found:** install Python and reopen your terminal,
  or use the command/path for your installed Python interpreter.
- **`No module named PIL`:** run `make install` or the manual dependency
  installation command, and start the app with the `.venv` Python.
- **Tkinter is missing:** install Tk support for your Python distribution. On
  Debian/Ubuntu, the relevant system packages are typically `python3-tk` and
  `python3-venv`. The `tk` package in `requirements.txt` does not install the
  system Tkinter runtime.
- **No window appears in a remote/headless terminal:** run the application in a
  graphical desktop session.
- **Saving PNG/JPEG fails with a Ghostscript error:** the app converts a
  PostScript export with Pillow. Install Ghostscript and make its executable
  available on `PATH`, then restart the app. It is not needed to open the app
  or draw.
