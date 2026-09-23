# Add color and thickness toolbar

## Overview and current behavior

Add a permanent horizontal toolbar directly below File, Select, View, and Help and above the drawing canvas. It must show the selected color as a clickable square and the shared tool thickness as a horizontal bar with a small vertical draggable thumb and a visible percentage from 0% to 100%.

Currently `DrawingBoardApp` in `main.py` constructs the menu and then packs the drawing canvas. Color is available through `select_color()` and Ctrl+Shift+C; thickness is available through `_change_size()` and keyboard shortcuts. There is no persistent display or mouse control for these settings. `pencil_size` is an integer from `MIN_PENCIL_SIZE` (1) to `MAX_PENCIL_SIZE` (50), shared by pencil, rubber, and new figure borders. `FigureTool.change_width()` in `figure_tool.py` also updates the selected figure in figure mode and records an undo entry on each effective update.

## Scope and assumptions

- Preserve the existing menus, shortcuts, drawing canvas dimensions, default size, color policy, and shared size limits.
- Interpret 0–100% as normalized position within the existing 1–50 pixel range: 0% means the minimum usable width, not an invisible zero-pixel stroke. This is an explicit design assumption.
- Clicking the color square opens the existing native Drawing Color picker, just like Select → Color. It does not open a new custom palette.
- The square shows `line_color`, including in rubber mode, because this is the retained color for future pencil marks and figures. It does not show an eraser background color or the selected figure's historical color.
- The percentage reflects the global size preference, even after undo restores a selected figure's previous border width.
- Use existing Tkinter/ttk facilities; no new dependency, persistence, file format, or setup requirement is expected.
- Exclude changing selected figures' colors, recoloring existing pencil marks, changing the size range, replacing the menu, and redesigning unrelated windows.
- No blocking open questions remain; the assumptions above should be documented in the delivered UI guidance.

## Acceptance criteria

1. On startup, a compact strip spans the area below the menu and above the canvas. The color square, horizontal thickness track, vertical thumb, and percentage are visible without opening another window. Existing canvas drawing space is preserved.
2. The square shows the effective drawing color immediately at startup, after picker acceptance, and after a theme change. It has a visible boundary for black and white colors. Clicking it opens the existing picker initialized to the current color.
3. Picker cancellation preserves color, default/custom policy, tool, thickness, artwork, and history. Accepting a color keeps existing future-artwork semantics. Return keyboard focus to the canvas when the picker closes.
4. Dragging the vertical thumb updates the integer thickness and percentage continuously, clamped to 1–50 pixels. Both endpoints and every integer size are reachable. Out-of-track drags remain bounded. Initial 1-pixel thickness displays 0%; 50 pixels displays 100%.
5. Existing size shortcuts and aliases still adjust by one pixel and immediately synchronize the thumb, label, cursor preview, and effective selected figure border. Programmatic synchronization never creates a recursive change or an extra undo entry.
6. Switching tools preserves settings. New pencil segments, rubber operations, and new figure borders use the chosen width. Toolbar interaction never creates pencil dots, eraser marks, or canvas history items.
7. In figure mode, one completed slider drag changes the selected figure's border as one `figure_update` action, irrespective of motion-event count. Unchanged final figures create no history entry. Undo restores the original figure width while retaining the global size and toolbar display. Existing keyboard edits remain one undo action per effective command.
8. Starting toolbar interaction stops active drawing without committing a dot and cancels pending figure placement/transform gestures. Slider release outside the track completes safely. Escape or interruption by a tool switch/dialog cancels an unfinished slider gesture and restores its initial global size and affected figure snapshot without adding history. Finalize or cancel before undo and Undo All dispatch so no stale transaction survives.
9. The strip is outside the artwork canvas, is absent from PNG/JPEG exports, and survives Undo All unchanged. Existing export success/failure cleanup, figure decorations, image preservation, and confirmation behavior remain intact.
10. Labels remain readable under both canvas themes and at normal desktop scaling; Help documents the controls and percentage meaning. Existing shortcuts remain usable after interacting with the strip.

## Branch preparation

Before changing implementation code, check working-tree state and preserve all local work, including this specification. Verify `main`, its configured remote and tracking branch; fetch and update `main` safely from that remote when available. Create a new branch from that verified `main` named exactly `add-color-and-thickness-toolbar`.

If `main` is missing, diverged, or the proposed branch already exists, inspect and resolve without overwriting work or silently selecting another base. Preserve the specification when switching branches. Do not reset or discard unrelated changes.

## Implementation plan

1. In `main.py`, add toolbar construction and synchronization helpers. Pack its container before the artwork canvas; initialize callbacks only when dependent canvas and figure-controller state is ready. Use English labels such as Color and Thickness. Keep swatch/track widgets separate from `self.canvas`, so export and artwork searches cannot include them.
2. Use a horizontal scale or a small dedicated control with a clearly vertical thumb. Confirm its rendered appearance on Windows before selecting the final widget; native themes may render scale thumbs differently. Keep the implementation small, provide keyboard focus/activation for the swatch and thickness control, and ensure the control does not swallow existing Ctrl shortcuts.
3. Centralize size application so shortcuts and the slider share clamping, cursor refresh, figure updates, and toolbar refresh. Retain `_change_size(delta)` as the keyboard entry point if useful. Use guarded programmatic updates so widget callbacks cannot recursively edit state or append history.
4. Make pixel width the authoritative value. For a normalized pointer position `p`, clamp to [0, 100] and calculate `size = MIN + floor((p / 100) * (MAX - MIN) + 0.5)`. Display `floor(100 * (size - MIN) / (MAX - MIN) + 0.5)` followed by `%`, and position the thumb from the same size. Percentage rounding means not every whole percentage corresponds to a distinct pixel size; for example, 25 pixels displays 49% and 26 pixels displays 51%. Do not maintain a separate inconsistent percentage preference.
5. Wire the square to `select_color()` and refresh the toolbar from successful color selection and `switch_theme()`. Keep explicit black/white selections fixed across themes; default colors follow the theme. Preserve cancellation and return focus after the dialog closes.
6. Add a bounded slider transaction around press/motion/release. Capture starting size and, when applicable, selected figure ID and immutable snapshot. Cancel pre-existing drawing/figure gestures first. Preview width changes on the existing figure canvas ID without recording every motion; on release, record one before/after update only if changed. Extend `FigureTool` with narrowly scoped preview/commit support rather than appending then deleting history records. Preserve geometry, stacking, and default/custom color metadata.
7. Route Escape and interruption through transaction cleanup. Restore starting size and affected figure on canceled slider gestures; preserve existing unrelated undo history. On undo/Undo All cancel an unfinished slider transaction before executing the established command. Ensure focus loss or a release outside the track cannot leave a stale active transaction. Keep keyboard size changes independent from drag batching.
8. Update Help in `main.py`, maintaining its scrolling, logo references, and dismissal behavior. No changes should be necessary to `eraser.py` or pure figure geometry in `figures.py`.

## Unit tests and validation

Implement and execute tests using the existing `unittest` / `unittest.mock` framework. Extend constructor mocks for newly introduced widgets and variables in every affected fixture; do not make headless tests depend on a real Tk root. Reuse the stateful canvas integration in `tests/test_figures.py` for actual history and figure-state assertions.

- `tests/test_main.py`: initial strip state; endpoint, interior rounding, and out-of-range conversion; all integer sizes reachable; picker acceptance/cancellation; default versus custom colors through theme changes; menu/shortcut and slider synchronization; no callback recursion; limits; shared size across tools; focus restoration; no accidental drawing on toolbar actions; Help content.
- `tests/test_figures.py`: many slider motions produce one update; no-op and return-to-start drags produce none; undo restores original width without resetting global size; cancellation restores the snapshot and size; keyboard edits remain independent; geometry, stacking, and color policy survive changes; interaction cancels pending placement/transform; mixed image/rubber/figure undo ordering remains valid.
- Cover release outside the track and interrupted drags, export success/failure and Undo All while interacting, plus toolbar absence from canvas export. Retain existing pencil-dot, rubber, image, and export cleanup regression coverage.

Run the full suite from the repository root:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
```

`make test` is the repository alternative; macOS/Linux use `.venv/bin/python -m unittest discover -v`. Run `git diff --check`. Record actual commands and results, resolve failures, and never report unrun checks as passed.

Launch with `.\.venv\Scripts\python.exe main.py` on a graphical desktop. Verify strip placement, square contrast, vertical thumb appearance, both endpoints, live cursor width, fast/outside-track drags, focus/keyboard behavior, both themes, dialog cancellation, selected-figure undo, and interruption cleanup. Check readable layout at desktop scaling and window resizing. With Ghostscript available, export PNG and JPEG and inspect that only artwork is included and selection decorations return. Capture a screenshot for the visible UI change. Report unavailable platform/export checks explicitly.

## Repository documentation

Review all repository documentation and update every affected document. In particular:

- `README.md`: overview, new toolbar usage, Pencil cursor and size, Rubber, Standard figures, and relevant screenshots; explain normalized percentages, shared width, and single-action slider undo.
- `doc/SETUP.md`: extend automated/manual validation guidance for toolbar interactions; retain setup commands unless implementation actually changes them.
- `AGENTS.md`: update component descriptions and UI invariants to capture synchronization and drag transaction semantics.
- `doc/FIGURES_VALIDATION.md`: review as a historical validation record; do not rewrite old results as evidence for this change. Record new validation separately if needed (a new validation document would be a proposed file).
- Review existing specifications as historical context; avoid rewriting unrelated feature scope. Keep unaffected documentation unchanged and record that decision after review.

## Completion checklist

- [ ] New implementation branch created from verified `main`, preserving local work and this spec.
- [ ] Acceptance criteria implemented, including color policy, normalization, and slider undo/cancellation.
- [ ] Meaningful unit tests added and executed; full suite and whitespace checks pass.
- [ ] GUI behavior and export manually verified where available; screenshot captured.
- [ ] All repository documentation reviewed and affected guidance updated.
- [ ] Actual validation results and material limitations or unresolved blockers reported.

This document is an implementation guide only. Specification drafting does not implement the toolbar, create the implementation branch or GitHub issue, or execute validation tests.
