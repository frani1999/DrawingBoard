# Standard figures validation

Validated on Windows with Python 3.10 on 2026-09-23, on branch
`add-standard-figures`. The branch was created from `main` after fetching origin
and verifying `main...origin/main` had zero commits on either side. The existing
untracked specification under `specs/5/` was preserved.

## Automated checks

Command from the repository root:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
```

Result: **74 tests passed** (54 existing tests and 20 new tests). Tests include
all three figure geometries, local/world transforms, rotation, resizing,
no-op and canceled gestures, shared width, default/custom color policy,
mixed history, image preservation, rubber exclusion, chooser lifecycle, and
export cancellation and failure cleanup. Regression tests also cover clicking
off-center on a rotated resize handle and keeping handles above imported images.

`git diff --check` reported no whitespace errors. Git emitted only its existing
LF-to-CRLF conversion notices. No dependencies or setup commands changed.

## Desktop checks

Checked in the running Tkinter app using Windows computer-use controls:

- Ctrl+Shift+F opened the chooser with Rectangle, Ellipse, Triangle,
  Edit existing figures, and Cancel.
- Placed a noncircular ellipse, rotated it by an arbitrary angle, and resized
  it in its rotated axes. The center stayed fixed.
- Ctrl+numpad+ changed its border width. Ctrl+Z restored the previous width
  and then the previous dimensions while retaining the rotation.
- Ctrl+H opened the existing Help window; its scrollbar exposed the complete
  Figures section and Close returned to the board.
- Saved real PNG and JPEG files through the native Save As dialog and Pillow /
  Ghostscript. Both succeeded. Inspected both outputs: the rotated outline was
  present, and selection borders, handles, and cursor decorations were absent.
- Editing handles were restored after export.

The screenshot in [`media/figures.png`](../media/figures.png) shows the real app
with a selected rotated ellipse. The final pointer-offset and import-stacking
corrections were verified by regression tests after the desktop session began.

## Validation limits

Desktop checks were performed on Windows only. Rectangle/triangle geometry,
size limits, custom colors/themes, mixed image/rubber history, and Undo All were
covered by automated tests; the full cross-product of those cases was not
repeated manually. Leaving the window during a drag was not manually exercised.
Tkinter's normal implicit mouse grab is used for drag/release delivery.

All affected guidance was reviewed: README.md, doc/SETUP.md, and AGENTS.md were
updated. The specification remains the original implementation reference.
