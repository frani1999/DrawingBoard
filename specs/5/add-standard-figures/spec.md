# Add standard figures

## Overview and repository context

Add standard geometric figures to DrawingBoard using the selected drawing color and shared pencil/rubber size for their border width. Open a figure chooser from **Select → Figures** or **Ctrl+Shift+F**. Figures must remain resizable and rotatable after insertion. Update the existing information/help window, unit tests, and affected documentation.

Current implementation:

- `main.py` owns `DrawingBoardApp`, menus, event bindings, tool state, colors, size, undo, Help, and import/export. There is no figure model or selection/transform mode.
- `pencil_size` is shared by pencil and rubber, starts at 1, and is constrained to 1–50 pixels. Existing increment/decrement shortcuts include Ctrl+= and numeric keypad variants.
- Default-colored artwork carries `theme_color`; explicitly selected colors remain fixed across themes.
- `items` contains canvas IDs and untyped rubber dictionaries with `erased` pairs. `undo()` currently assumes every dictionary is a rubber action.
- `_erase_to()` currently considers every canvas line a pencil segment, and `remaining_segments()` in `eraser.py` accepts exactly two endpoints. Figure polylines must not accidentally reach that helper.
- `switch_theme()` currently recolors the `fill` option. Figure rendering must account for whether border color uses `fill` or `outline`.
- `save_draw()` exports canvas PostScript through Pillow and hides the three existing cursor decorations. Figure editing decorations must also be excluded.
- `show_help()` builds a reusable Toplevel titled `Drawing Board Help`; this is the existing information window meant by the request, not a new parallel help dialog.
- Tests use `unittest`/`unittest.mock` in `tests/test_main.py` and geometry/stateful canvas tests in `tests/test_eraser.py`.

## Scope and explicit assumptions

User requirements are the chooser/menu/shortcut, selected color, adjustable shared border width, resizing, rotation, Help, tests, documentation review, and an implementation branch.

The following are proposed defaults because the request does not define these interactions. They are implementation assumptions, not additional confirmed user requirements:

1. Initial catalog: **Rectangle, Ellipse, Triangle**, all with transparent interiors. Square and circle can be made through equal dimensions; additional shapes and fill controls are outside this iteration.
2. Choosing a figure enters a figure tool. Drag on empty canvas to set its initial bounds; release commits one figure. A zero-width or zero-height gesture creates nothing. Negative-direction drags normalize the bounds.
3. Figures remain editable in figure mode. Clicking a visible figure border selects it; overlapping hits choose the topmost figure. Empty clicks deselect. Pencil and rubber keep their existing interactions.
4. A selected figure has four corner resize handles and a distinct rotation handle. Resize along its local axes around its fixed center, with a minimum dimension of 1 canvas pixel; crossing the center clamps rather than mirrors. Rotate continuously around its center. Resizing retains the angle and does not scale border width. Rectangles and ellipses may have independent width and height.
5. The chooser also provides an **Edit existing figures** action so returning to editing does not require inserting artwork. After selecting a catalog entry, clicking an existing border selects it; dragging empty space inserts the chosen type. In edit-only mode, empty drags do nothing.
6. New figures inherit current color, default/custom color status, and `pencil_size`. Size shortcuts in figure mode also update the selected figure's border; outside figure mode they affect future drawing only. Color selection affects future figures and strokes, matching current pencil behavior. Existing default-colored figures follow theme changes; custom colors, including black and white, stay fixed.
7. Rubber preserves figures as editable objects, just as it preserves images; it continues erasing pencil marks. Partial figure erasure is excluded. Confirmed Undo All removes figures along with pencil marks and drawing/edit history, preserving imported images and their undo order.
8. Moving figures, multi-selection, redo, snapping, filled shapes, and editable project serialization are excluded. Existing PNG/JPEG export includes committed figures as rendered artwork.

No dependency change is expected: use existing Tkinter/Pillow and Python standard-library geometry. These assumptions should be revisited if the user supplies a different catalog or editing policy; no external service or migration is needed.

## Acceptance criteria

- Select contains Figures with the Ctrl+Shift+F accelerator, and that shortcut invokes the same reusable chooser. Reopening raises/focuses it rather than spawning duplicates.
- The chooser clearly labels all three types and edit-only mode. Cancel, Escape, and window close preserve committed artwork, tool settings, and history and restore canvas focus. Opening it stops active pencil/rubber gestures without creating a pencil dot; an unfinished figure gesture is canceled safely.
- Every type can be inserted in any drag direction with the selected color and current shared border size. Preview items never enter history; release adds one undoable figure. Degenerate/canceled placement adds nothing.
- Figures can be reselected, resized repeatedly, and rotated through arbitrary angles. A rotated ellipse visibly rotates when its axes differ. Handle hit testing takes priority over figure selection; hidden objects and decorations are never selectable artwork.
- A completed resize or rotation contributes one undo action, regardless of motion-event count. No-op and canceled gestures add none. Escape restores the exact pre-gesture model. Switching tools cancels unfinished transforms and clears selection decorations.
- Ctrl+Z restores the prior figure geometry or border width, then can remove figure creation, in chronological order alongside pencil marks, rubber actions, and imports. Selection changes do not enter history.
- Shared size remains 1–50 pixels with the existing shortcut aliases and preserves values across tools. One effective border-size shortcut change is undoable; a limit/no-op change is not. Undo restores artwork width without rolling back the global tool-size preference.
- Theme switching updates default-colored figure borders, including any later restored undo state, without filling interiors or recoloring custom artwork or imports.
- Rubber ignores figures, handles, and previews. Pencil dot/line behavior and rubber cuts/undo remain correct.
- Undo All retains the exact existing OK/Cancel question and default Cancel. Cancel preserves committed figures and history; OK removes all figures and their history while preserving image references, imported-image undo order, cursor decorations, and tool/theme preferences. Pending gestures are canceled before the dialog.
- Saved PNG/JPEG output includes transformed figures and excludes selection outlines, handles, cursor decorations, and insertion previews. Export cancellation/failure leaves committed artwork and selection usable; export cleanup restores the correct editing UI on success and failure.
- Existing Help documents figure selection, placement, re-editing, resizing, rotation, cancellation, border width, rubber policy, and undo. It retains its logo, reusable window, bold commands, and Close/Escape/Enter focus behavior without clipping added content.

## Branch preparation

Before implementation code changes, create a new branch from `main` named exactly **`add-standard-figures`**. This specification task does not create that branch.

1. Check working-tree state and preserve all local work, including this spec. Do not reset, overwrite, or silently stash unrelated edits.
2. Inspect the configured remote and tracking branch. Fetch and verify/update `main` from its configured remote when available; use a safe fast-forward and resolve divergence explicitly. Record when no remote is configured or an update cannot be verified.
3. Create `add-standard-figures` from the verified `main` base. If `main` is missing or that branch already exists, inspect and resolve without overwriting existing work or silently choosing another base.
4. Preserve this specification across any branch switch. At drafting time the current branch was `main` and the working tree was clean before adding the spec; recheck at implementation time.

## Implementation plan

1. **Introduce geometry and figure state.** Proposed new `figures.py`: keep geometry independent of Tkinter, following `eraser.py`. Store stable figure identity, kind, center, local width/height, rotation, border width, color, and default/custom status. Generate transformed coordinates from canonical geometry, not repeatedly rounded canvas coordinates. Provide local/world conversion and border/handle hit testing. Handle zero-length pointer vectors without division errors.
2. **Render editable figures.** In `main.py`, maintain a registry associating figure identities with canvas items. A proposed common rendering strategy is closed line paths, sampling ellipses finely enough to appear smooth at canvas/export resolution. Verify seams and joins manually. Keep rendering strategy encapsulated so it can change without altering the model. Use explicit figure/artwork/decoration tags. Exclude figure paths from `_erase_to()` before passing coordinates to `remaining_segments()`.
3. **Add chooser and tool dispatch.** Extend `_build_menu()`, `_bind_events()`, `_select_tool()`, and cursor/event handlers for figure mode. Do not rely on the current pencil-versus-rubber binary branches: `draw()` otherwise falls through to pencil drawing, and `_select_tool()` assumes every non-pencil tool uses the rubber cursor. Add reusable chooser lifecycle and return `break` from keyboard callbacks where appropriate. Keep chooser selection changes pending until a user action accepts them.
4. **Implement gestures as transactions.** Track placement, selected identity, gesture type, initial model, and current preview separately. Transform from the initial model on each motion; commit once on release. Escape/tool changes/chooser opening cancel in-flight figure operations. Dialog actions, imports, undo, Undo All, and export must settle/cancel pending gestures consistently before operating on committed artwork. Selection adornments stay above artwork and never enter history. Leaving/re-entering the canvas must not leave a stuck gesture; test real Tk release behavior.
5. **Extend undo explicitly.** Add distinguishable figure-create and figure-update action records; retain support for existing canvas IDs and rubber records or migrate all action handling coherently. Dispatch by action type rather than treating all dictionaries as erasures. Store before/after model snapshots and restore geometry, style policy, registry, and original stacking consistently. Resolve default colors against the current theme when restoring a snapshot. Undo creation removes every associated rendering/selection item.
6. **Integrate shared size and theme.** Reuse `pencil_size` and existing limits rather than add an independent border-size preference. Apply effective size changes to a selected figure only in figure mode; preserve figure border width during resize. Adapt theme rendering for figure border options and avoid restoring stale resolved colors during undo.
7. **Integrate Undo All and export.** Teach Undo All to clear figure objects/actions without removing imported images or losing their references. Centralize temporary-decoration visibility as needed. Export must include only committed artwork and restore active selection/cursor state in cleanup, including failures in PostScript generation, conversion, and file save. Preserve current temporary-file/background cleanup.
8. **Update Help and documentation.** Extend existing `show_help()` rather than introduce another information window. If added content exceeds screen height, provide an accessible layout/scrolling while retaining focus and close behavior. Update tests and the documents listed below in the same implementation.

## Unit tests and validation

Implement and execute meaningful unit tests. Proposed `tests/test_figures.py` covers pure geometry plus stateful canvas behavior; extend `tests/test_main.py` and `tests/test_eraser.py` for integration. Reuse or extract a small stateful canvas fake as appropriate; ensure it supports coordinate mutation, tags, visibility, and stacking rather than only asserting mocked calls.

- All catalog geometries, reversed placement bounds, degenerate gestures, 0/90/360-degree and arbitrary rotations, repeated transforms, rotated local-axis resizing, center/angle preservation, minimum dimensions, and border-width independence.
- Border hit/miss and topmost selection; handles winning over borders; imported images, pencil dots, hidden originals, and decorations excluded from figure selection.
- Chooser menu/binding equivalence, reuse, cancel/Escape/close, focus restoration, edit-only mode, and interruption of pending pencil clicks without unwanted dots.
- Creation/transform commits once; canceled/no-op operations leave history unchanged; selecting/reselecting works after tool changes. Test deleting a selected figure via undo and stale-selection cleanup.
- Shared size inheritance from both pencil and rubber, all aliases and limits, selected-figure width undo, color-picker cancellation, explicit black/white, theme round trips, and undo after a theme change.
- Mixed history of imports, pencil strokes/dots, figure creation/edits, and repeated rubber cuts. Undo restores the expected object state and stacking at each step. Rubber leaves all figure geometry intact, including paths with more than two endpoints.
- Undo All confirmation/cancel, active figure gestures, multiple figures/imports, empty and image-only boards, repeated calls, and later individual image undo.
- Export success, cancellation, PostScript/conversion/write failures: artwork remains intact and all temporary decorations are excluded/restored correctly. Help tests verify shortcut and documented interaction policy without merely snapshotting implementation details.

Run the entire suite from the repository root using `make test`, or on Windows `.\.venv\Scripts\python.exe -m unittest discover -v`. On macOS/Linux use `.venv/bin/python -m unittest discover -v`. Record actual commands/results and resolve failures; never report unrun checks as passing.

Manually run the app with the platform's `.venv` Python and `main.py`. Verify every chooser action, repeated editing after tool switches, visible arbitrary rotation of a noncircular ellipse, sizes 1 and 50, overlapping figures, theme changes, focus, cursor state, and Help fitting the screen. Exercise Undo All and real PNG/JPEG export with Ghostscript available, checking images for missing borders or leaked handles. Capture screenshots for visible UI changes. If desktop/export prerequisites are unavailable, report the specific unverified checks.

## Repository documentation

Review all repository documentation and update every affected document to match the final implemented interactions:

- `README.md`: overview, Select menu table, color/shared-size guidance, new figures usage section, undo/Undo All behavior, rubber policy, development/test coverage, and applicable screenshots/demo caveats.
- `doc/SETUP.md`: test coverage and manual checks for chooser, transforms, shared size, undo, Help, and export. Keep setup/dependency commands unchanged unless implementation actually changes prerequisites.
- `AGENTS.md`: module/test inventory and new invariants for figure mode, shared width, theme semantics, typed history, rubber exclusion, selection decorations, export, and Help. Preserve existing pencil/rubber and image invariants while explicitly extending Undo All to figures.
- Review any other documentation discovered during implementation, including spec references if its issue directory is renamed. Leave unaffected content unchanged and record when reviewed documents need no changes.

## Completion checklist

- [ ] Implementation branch created from verified `main` with local work preserved.
- [ ] Catalog and interaction assumptions implemented or explicitly revised with rationale.
- [ ] All acceptance criteria implemented, including undo/theme/rubber/export integration.
- [ ] Unit tests added and the full suite executed; actual results recorded and failures resolved.
- [ ] GUI and real export checks completed, or concrete limitations reported.
- [ ] Existing Help and all affected repository documentation updated.
- [ ] Screenshots supplied for visible interface changes; unresolved blockers or limitations reported.

Specification drafting only: no feature code, implementation branch, GitHub issue, or test execution is included in this task.
