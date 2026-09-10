# Drawing Board

<img src="media/logo.png" alt="Drawing Board logo: a pencil on a drawing board" width="96"/>

## 👁️ Overview

This project implements a simple drawing board based on [*Linkfy*](https://www.youtube.com/@Linkfydev) YouTube tutorial:
[*"Crea un Paint en Python | Fácil"*](https://youtu.be/mqv1n4lIExg?si=9YqUx_p-55iywy_m).

<img src="media/gif1.gif" alt="Demo" width="400"/>

Draw freehand lines or single-click dots, choose pencil colors, and erase marks
with a rubber tool. Both tools have size previews and share an adjustable size.
The app also supports black and white canvas themes, image import, PNG/JPEG
export, undo, and a formatted Help window with the Drawing Board logo.

The demo above shows an earlier version; the controls below describe the current app.

## Setup and run

See [SETUP.md](doc/SETUP.md) for prerequisites and step-by-step instructions for
Windows, macOS, and Linux. With Python and GNU Make installed, run `make setup`
once, then `make run` to open the application.

## 💻 Menu Bar functions

| Layer | Function     | keyboard shortcut | Info                                                                          |
|-------|--------------|-------------------|-------------------------------------------------------------------------------|
| File  | Save Drawing | **Ctrl+S**        | Save current drawing. <br/>User can select path, name and format (png or jpg) |
| File  | Import Image | **Ctrl+I**        | Import local image to draw                                                    |
| File  | Undo All     | **Ctrl+Shift+Z**  | Clear pencil marks after confirmation; keep imported images |
| File  | Exit         | -                 | Exit the application                                                          |
| Select | Color       | **Ctrl+Shift+C**  | Choose the pencil color for new strokes |
| Select | Pencil      | **Ctrl+Shift+P**  | Switch back to drawing |
| Select | Rubber      | **Ctrl+Shift+R**  | Erase pencil marks |
| View  | Switch Theme | **Ctrl+T**        | Switch between black and white theme                                          |
| Help  | Show Help    | **Ctrl+H**        | Show keyboard shortcuts help                                                  |

### Other keyboard shortcuts

- **Ctrl+Z** → Undo a drawing segment, dot, image import, or rubber stroke
- **Ctrl + + / -** → Increase or decrease the active tool size by 1 pixel

### Undo All

Choose **File → Undo All** (**Ctrl+Shift+Z**) to remove all pencil lines and dots
while keeping imported images. A warning asks **“Are You sure you want to undo all design?”**
Choose **OK** to accept or **Cancel** to keep the design; Cancel is selected by
default. This clears drawing and rubber history, so **Ctrl+Z cannot restore the
cleared marks**. Image imports remain in undo history and can still be undone
individually with **Ctrl+Z**.
The selected tool, size, color, and canvas theme stay unchanged.

### Drawing lines and dots

Drag on the canvas to draw with the pencil. Click and release without moving to
draw a round dot using the current size and color. Dots can be undone and erased
with the rubber. A normal drag does not add an extra dot when released.

### Pencil cursor and size

Use **Select → Color** (**Ctrl+Shift+C**) to select a pencil color. By default, the pencil is black
on the white theme and white on the black theme. Custom selections (including
black and white selected in the color picker) and strokes drawn with those colors
keep their color when switching themes. Earlier strokes drawn with the default
color continue to follow the theme. Canceling the picker keeps the current color.

The drawing canvas uses a pencil pointer with a circular outline that reflects
the current stroke width. The default size is **1 pixel**, with a minimum of
**1 pixel** and a maximum of **50 pixels**.

- **Ctrl + +** increases the size by 1 pixel.
- **Ctrl + -** decreases the size by 1 pixel.
- **Ctrl + =** and **Ctrl + numeric keypad + / -** also work.

Further adjustments at either limit leave the size unchanged. Size changes apply
to new drawing segments and update the cursor outline immediately. The outline
is only a preview and is excluded from saved images. These shortcuts and limits
are also available under **Help → Show Help** (**Ctrl+H**).

The Help window groups shortcuts and shared tool sizes into indented sections, with
bold shortcut commands. It uses the Drawing Board logo instead of an information
icon. Press **Escape**, **Enter**, or **Close** to dismiss it.

### Rubber

Choose **Select → Rubber** (**Ctrl+Shift+R**) to erase pencil marks by clicking
or dragging. The pointer changes to a rubber icon with a circular size outline.
Erasing cuts pencil segments, revealing the background or imported images beneath;
it does not paint over them. **Ctrl+Z** restores the last rubber stroke.

The pencil and rubber share one size: **1 pixel by default**, adjustable from
**1 to 50 pixels** with **Ctrl + + / -** (including the alternate size shortcuts
above). Switching tools keeps the current size, including changes made with the
rubber selected. Choose **Select → Pencil** (**Ctrl+Shift+P**) to resume drawing
with the previous pencil color. The rubber icon and size outline are excluded
from saved images.

## Development and tests

- `main.py`: Tkinter application, menus, Help, drawing tools, undo, and image I/O.
- `eraser.py`: geometry for cutting pencil segments along a rubber drag.
- `logo.py`: Pillow renderer for the application logo.
- `tests/test_main.py`: application, dialogs, drawing, dots, color, Help, and export tests.
- `tests/test_eraser.py`: rubber geometry and stateful canvas behavior tests.
- `media/logo.png`: logo used in this README; the app renders its icon at runtime.

Run `make test`, or use PowerShell from the repository root:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
```

On macOS/Linux, use `.venv/bin/python -m unittest discover -v`. Tests mock Tk
widgets, dialogs, and file I/O where needed, so they run without opening windows
or requiring Ghostscript. They cover size limits, tool switching, dots, custom
color preservation, rubber cuts and undo, Help, and export cleanup. Launch the
app to check cursor rendering and native dialogs manually; real image export
requires the prerequisites in [SETUP.md](doc/SETUP.md).

## 📄 Disclaimer

This project is an extension of the code extracted from 
[*"Crea un Paint en Python | Fácil"*](https://youtu.be/mqv1n4lIExg?si=9YqUx_p-55iywy_m) [*Linkfy´s*](https://www.youtube.com/@Linkfydev) video.

I am not the original author of the base code; I have only made modifications and improvements for educational and learning purposes.

## 🔗 References
* **Linkfy**, *Crea un Paint en Python | Fácil* → https://youtu.be/mqv1n4lIExg?si=9YqUx_p-55iywy_m
* **pythontutorial.net**, *Tkinter Menu* → https://www.pythontutorial.net/tkinter/tkinter-menu/
* **geeksforgeeks.org**, *Python Tkinter - MessageBox Widget* →  https://www.geeksforgeeks.org/python/python-tkinter-messagebox-widget/
* **Fabio Musanni - Programming Channel**, *Python Tkinter Menu Widget | Create Menu Bar in Tkinter | Menus & Submenus in Tkinter GUI App* → https://youtu.be/7Z2J7NdsCRc?si=IKqcsOv1FxS1cIdQ

