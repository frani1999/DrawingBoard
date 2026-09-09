"""Test application behavior without a display, dialogs, or Ghostscript."""

import os
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import call, patch

from PIL import Image

from main import BLACK, WHITE, MAX_PENCIL_SIZE, MIN_PENCIL_SIZE, DrawingBoardApp


class DrawingBoardTests(unittest.TestCase):
    def setUp(self):
        # Exercise the real constructor while keeping all Tk widgets headless.
        for target in ("main.tk.Tk", "main.tk.Canvas", "main.tk.Menu",
                       "main.ImageTk.PhotoImage", "main.tk.Toplevel",
                       "main.ttk.Frame", "main.ttk.Label", "main.ttk.Button",
                       "main.tkfont.nametofont"):
            patcher = patch(target)
            patcher.start()
            self.addCleanup(patcher.stop)
        dialog_patcher = patch("main.showinfo")
        self.showinfo = dialog_patcher.start()
        self.addCleanup(dialog_patcher.stop)
        self.app = DrawingBoardApp()
        self.canvas = self.app.canvas
        self.canvas.winfo_width.return_value = 800
        self.canvas.winfo_height.return_value = 600

    def test_drawing_tracks_connected_segments_and_undo_order(self):
        self.canvas.create_line.side_effect = [11, 12]
        self.app.start_drawing(SimpleNamespace(x=10, y=20))
        self.app.draw(SimpleNamespace(x=30, y=40))
        self.app.draw(SimpleNamespace(x=50, y=60))
        self.assertEqual(self.canvas.create_line.call_args_list, [
            call(10, 20, 30, 40, fill=BLACK, width=1, capstyle='round'),
            call(30, 40, 50, 60, fill=BLACK, width=1, capstyle='round'),
        ])
        self.assertEqual(self.app.items, [11, 12])
        self.assertEqual((self.app.last_x, self.app.last_y), (50, 60))

        self.app.undo()
        self.canvas.delete.assert_called_once_with(12)
        self.assertEqual(self.app.items, [11])

    def test_click_creates_dot_with_selected_size_color_and_undo(self):
        self.canvas.create_oval.reset_mock()
        self.canvas.create_oval.return_value = 123
        self.app.pencil_size = 10
        self.app.line_color = '#ff0000'
        self.app._custom_color = True
        event = SimpleNamespace(x=20, y=30)
        self.app.start_drawing(event)
        self.app.stop_drawing(event)
        self.canvas.create_oval.assert_called_once_with(
            15, 25, 25, 35, fill='#ff0000', outline='', tags=('pencil_dot',))
        self.assertEqual(self.app.items, [123])
        self.canvas.addtag_withtag.assert_not_called()
        self.app.undo()
        self.canvas.delete.assert_called_once_with(123)

    def test_stationary_motion_still_creates_one_default_dot(self):
        self.canvas.create_oval.reset_mock()
        self.canvas.create_oval.return_value = 123
        event = SimpleNamespace(x=20, y=30)
        self.app.start_drawing(event)
        self.app.draw(event)
        self.app.stop_drawing(event)
        self.app.stop_drawing(event)
        self.canvas.create_oval.assert_called_once_with(
            19.5, 29.5, 20.5, 30.5, fill=BLACK, outline='', tags=('pencil_dot',))
        self.canvas.addtag_withtag.assert_called_once_with('theme_color', 123)
        self.canvas.create_line.assert_not_called()

    def test_drag_release_does_not_add_extra_dot(self):
        self.canvas.create_oval.reset_mock()
        self.app.start_drawing(SimpleNamespace(x=10, y=20))
        self.app.draw(SimpleNamespace(x=30, y=40))
        self.app.stop_drawing(SimpleNamespace(x=30, y=40))
        self.canvas.create_oval.assert_not_called()

    def test_tool_switch_does_not_commit_unreleased_dot(self):
        self.canvas.create_oval.reset_mock()
        self.app.start_drawing(SimpleNamespace(x=10, y=20))
        self.app.select_rubber()
        self.app.stop_drawing(SimpleNamespace(x=10, y=20))
        self.canvas.create_oval.assert_not_called()

    def test_draw_ignores_motion_before_press_and_after_release(self):
        event = SimpleNamespace(x=20, y=30)
        self.app.draw(event)
        self.app.start_drawing(event)
        self.app.stop_drawing()
        self.app.draw(event)
        self.canvas.create_line.assert_not_called()
        self.assertEqual(self.app.items, [])
        self.assertFalse(self.app.is_drawing)

    def test_missing_events_do_not_start_or_modify_drawing(self):
        self.app.start_drawing()
        self.assertFalse(self.app.is_drawing)
        self.app.start_drawing(SimpleNamespace(x=10, y=20))
        self.app.draw()
        self.canvas.create_line.assert_not_called()
        self.assertEqual((self.app.last_x, self.app.last_y), (10, 20))

    def test_undo_empty_board_is_safe(self):
        self.app.undo()
        self.canvas.delete.assert_not_called()
        self.assertEqual(self.app.items, [])

    def test_theme_round_trip_recolors_only_lines(self):
        self.canvas.find_withtag.return_value = [11]
        self.app.switch_theme()
        self.assertEqual((self.app.background_color, self.app.line_color), (BLACK, WHITE))
        self.canvas.configure.assert_called_with(background=BLACK)
        self.canvas.itemconfig.assert_called_once_with(11, fill=WHITE)

        self.app.switch_theme()
        self.assertEqual((self.app.background_color, self.app.line_color), (WHITE, BLACK))
        self.canvas.configure.assert_called_with(background=WHITE)
        self.assertEqual(self.canvas.itemconfig.call_args_list, [
            call(11, fill=WHITE), call(11, fill=BLACK),
        ])

    def test_new_lines_use_selected_theme_color(self):
        self.app.switch_theme()
        self.app.start_drawing(SimpleNamespace(x=1, y=2))
        self.app.draw(SimpleNamespace(x=3, y=4))
        self.canvas.create_line.assert_called_once_with(
            1, 2, 3, 4, fill=WHITE, width=1, capstyle='round')

    def test_default_color_matches_initial_theme(self):
        for background, expected in ((WHITE, BLACK), (BLACK, WHITE)):
            with self.subTest(background=background):
                app = DrawingBoardApp(bg_color=background)
                self.assertEqual(app.line_color, expected)
                self.assertFalse(app._custom_color)

    def test_select_menu_opens_color_selector(self):
        import main
        main.tk.Menu.return_value.add_cascade.assert_any_call(
            menu=main.tk.Menu.return_value, label='Select')
        main.tk.Menu.return_value.add_command.assert_any_call(
            label='Color', accelerator='Ctrl+Shift+C', command=self.app.select_color)

    @patch('main.colorchooser.askcolor', return_value=((255, 0, 0), '#ff0000'))
    def test_selected_color_updates_new_lines_and_cursor(self, chooser):
        self.app._move_cursor(SimpleNamespace(x=10, y=20))
        self.app.select_color()
        chooser.assert_called_once_with(
            color=BLACK, parent=self.app.window, title='Pencil Color')
        self.canvas.itemconfigure.assert_called_with(
            self.app._cursor_outline, outline='#ff0000', state='normal')
        self.app.start_drawing(SimpleNamespace(x=10, y=20))
        self.app.draw(SimpleNamespace(x=30, y=40))
        self.canvas.create_line.assert_called_with(
            10, 20, 30, 40, fill='#ff0000', width=1, capstyle='round')
        self.canvas.addtag_withtag.assert_not_called()
        self.canvas.itemconfig.assert_not_called()

    @patch('main.colorchooser.askcolor', return_value=(None, None))
    def test_cancel_color_preserves_default_or_custom_selection(self, chooser):
        for custom, color in ((False, BLACK), (True, '#123456')):
            with self.subTest(custom=custom):
                self.app._custom_color = custom
                self.app.line_color = color
                self.app.select_color()
                self.assertEqual(self.app.line_color, color)
                self.assertEqual(self.app._custom_color, custom)
        self.canvas.itemconfigure.assert_not_called()

    def test_theme_preserves_custom_colors_including_selected_black_and_white(self):
        for color in ('#ff0000', '#000000', '#ffffff'):
            with self.subTest(color=color):
                self.canvas.reset_mock()
                self.canvas.create_line.side_effect = [11, 12]
                self.canvas.find_withtag.return_value = [11]
                self.app._custom_color = False
                self.app.start_drawing(SimpleNamespace(x=1, y=2))
                self.app.draw(SimpleNamespace(x=3, y=4))
                self.canvas.addtag_withtag.assert_called_once_with('theme_color', 11)
                with patch('main.colorchooser.askcolor', return_value=((0, 0, 0), color)):
                    self.app.select_color()
                self.app.start_drawing(SimpleNamespace(x=3, y=4))
                self.app.draw(SimpleNamespace(x=5, y=6))
                self.app.switch_theme()
                self.assertEqual(self.app.line_color, color)
                self.app.switch_theme()
                self.assertEqual(self.app.line_color, color)
                self.assertEqual(self.canvas.itemconfig.call_args_list, [
                    call(11, fill=WHITE), call(11, fill=BLACK)])
                self.canvas.find_withtag.assert_called_with('theme_color')

    def test_explicit_constructor_color_survives_theme_change(self):
        app = DrawingBoardApp(line_color='red')
        app.switch_theme()
        self.assertEqual(app.line_color, 'red')

    def test_pencil_cursor_and_shortcuts(self):
        import main
        self.assertEqual(main.tk.Canvas.call_args.kwargs['cursor'], 'pencil')
        bindings = dict(c.args for c in self.app.window.bind.call_args_list)
        for key in ('plus', 'equal', 'KP_Add'):
            self.assertEqual(bindings[f'<Control-{key}>'], self.app.increase_pencil_size)
        for key in ('minus', 'KP_Subtract'):
            self.assertEqual(bindings[f'<Control-{key}>'], self.app.decrease_pencil_size)

    def test_size_steps_and_limits(self):
        self.assertEqual(self.app.pencil_size, MIN_PENCIL_SIZE)
        self.app.decrease_pencil_size()
        self.assertEqual(self.app.pencil_size, MIN_PENCIL_SIZE)
        self.assertEqual(self.app.increase_pencil_size(), 'break')
        self.assertEqual(self.app.pencil_size, MIN_PENCIL_SIZE + 1)
        for _ in range(MAX_PENCIL_SIZE + 5):
            self.app.increase_pencil_size()
        self.assertEqual(self.app.pencil_size, MAX_PENCIL_SIZE)
        self.app.decrease_pencil_size()
        self.assertEqual(self.app.pencil_size, MAX_PENCIL_SIZE - 1)
        for _ in range(MAX_PENCIL_SIZE + 5):
            self.app.decrease_pencil_size()
        self.assertEqual(self.app.pencil_size, MIN_PENCIL_SIZE)

    def test_outline_tracks_size_theme_and_leave(self):
        self.app._move_cursor(SimpleNamespace(x=20, y=30))
        self.app.increase_pencil_size()
        self.canvas.coords.assert_called_with(self.app._cursor_outline, 19, 29, 21, 31)
        self.app.switch_theme()
        self.canvas.itemconfigure.assert_called_with(
            self.app._cursor_outline, outline=WHITE, state='normal')
        self.app._hide_cursor()
        self.canvas.itemconfigure.assert_any_call(self.app._cursor_outline, state='hidden')
        self.canvas.coords.reset_mock()
        self.app.increase_pencil_size()
        self.canvas.coords.assert_not_called()
        self.assertEqual(self.app.items, [])

    def test_drawing_uses_current_size_and_moves_outline(self):
        self.app.increase_pencil_size()
        self.app.start_drawing(SimpleNamespace(x=10, y=20))
        self.app.draw(SimpleNamespace(x=30, y=40))
        self.canvas.create_line.assert_called_once_with(
            10, 20, 30, 40, fill=BLACK, width=2, capstyle='round')
        self.canvas.coords.assert_called_with(self.app._cursor_outline, 29, 39, 31, 41)
        self.canvas.tag_raise.assert_called_with(self.app._cursor_outline)

    def test_export_hides_outline_and_restores_after_success_or_failure(self):
        self.prepare_save()
        self.app._move_cursor(SimpleNamespace(x=20, y=30))
        for failure in (False, True):
            with self.subTest(failure=failure):
                def export(**kwargs):
                    self.canvas.itemconfigure.assert_any_call(
                        self.app._cursor_outline, state='hidden')
                    if failure:
                        raise OSError('export failed')
                self.canvas.postscript.side_effect = export
                self.app.save_draw()
                self.canvas.itemconfigure.assert_called_with(
                    self.app._cursor_outline, outline=BLACK, state='normal')

    def test_help_documents_pencil_shortcuts_and_limits(self):
        import main
        self.app.show_help()
        labels = main.ttk.Label.call_args_list
        text = '\n'.join(c.kwargs.get('text', '') for c in labels)
        for expected in ('Ctrl++', 'Ctrl+-', 'Minimum: 1 pixel',
                         'Maximum: 50 pixels', 'Default: 1 pixel', 'outline', 'limit',
                         'PNG or JPEG', 'Ctrl+Shift+C', 'Ctrl+Shift+R',
                         'Ctrl+Shift+P', 'Both tools share the size'):
            self.assertIn(expected, text)
        self.showinfo.assert_not_called()
        for label in labels:
            if label.kwargs.get('text', '').startswith('Ctrl+') and '\n' not in label.kwargs['text']:
                self.assertIs(label.kwargs['font'], self.app._help_window.bold_font)
        self.app._help_window.bold_font.configure.assert_called_with(weight='bold')

    def test_save_excludes_rubber_cursor_and_restores_it_after_failure(self):
        self.prepare_save()
        self.app.select_rubber()
        self.app._move_cursor(SimpleNamespace(x=20, y=30))
        for failure in (False, True):
            with self.subTest(failure=failure):
                self.canvas.itemconfigure.reset_mock()

                def export(**kwargs):
                    for item in (self.app._cursor_outline, self.app._rubber_icon,
                                 self.app._rubber_sleeve):
                        self.canvas.itemconfigure.assert_any_call(item, state='hidden')
                    if failure:
                        raise OSError('export failed')

                self.canvas.postscript.side_effect = export
                self.app.save_draw()
                for item in (self.app._rubber_icon, self.app._rubber_sleeve):
                    self.canvas.itemconfigure.assert_any_call(item, state='normal')

    def test_help_reuses_window_and_close_restores_canvas_focus(self):
        import main
        self.app.show_help()
        dialog = self.app._help_window
        self.app.show_help()
        main.tk.Toplevel.assert_called_once_with(self.app.window)
        dialog.lift.assert_called_once()
        bindings = dict(c.args for c in dialog.bind.call_args_list)
        self.assertEqual(bindings['<Escape>'], self.app._close_help)
        self.assertEqual(bindings['<Return>'], self.app._close_help)
        dialog.protocol.assert_called_once_with('WM_DELETE_WINDOW', self.app._close_help)
        self.app._close_help()
        dialog.destroy.assert_called_once()
        self.assertIsNone(self.app._help_window)
        self.canvas.focus_set.assert_called_once()
        self.app._close_help()
        dialog.destroy.assert_called_once()

    def test_logo_is_used_for_main_and_help_windows(self):
        self.app.window.iconphoto.assert_called_once_with(True, self.app._logo)
        self.app.show_help()
        self.app._help_window.iconphoto.assert_called_once_with(False, self.app._logo)

    def test_logo_renders_at_icon_sizes(self):
        from logo import create_logo
        for size in (16, 32, 64, 256):
            with create_logo(size) as logo:
                self.assertEqual(logo.size, (size, size))
                self.assertEqual(logo.mode, 'RGBA')
                self.assertIsNotNone(logo.getbbox())

    @patch("main.Image.open")
    @patch("main.filedialog.askopenfilename", return_value="")
    def test_cancel_import_leaves_board_unchanged(self, dialog, open_image):
        self.app.import_image()
        open_image.assert_not_called()
        self.canvas.create_image.assert_not_called()
        self.assertEqual(self.app.items, [])
        self.assertEqual(self.app._image_refs, [])

    @patch("main.Image.open", side_effect=OSError("invalid image"))
    @patch("main.filedialog.askopenfilename", return_value="broken.png")
    def test_unreadable_import_reports_error_without_adding_item(self, dialog, open_image):
        self.app.import_image()
        self.showinfo.assert_called_once_with(
            "Import error", "Cannot open Image broken.png: invalid image"
        )
        self.canvas.create_image.assert_not_called()
        self.assertEqual(self.app.items, [])
        self.assertEqual(self.app._image_refs, [])

    def test_import_preserves_aspect_ratio_and_never_enlarges_images(self):
        cases = [
            ((1600, 400), (800, 200)),
            ((400, 1200), (200, 600)),
            ((1600, 1200), (800, 600)),
            ((800, 600), (800, 600)),
            ((100, 50), (100, 50)),
        ]
        for original_size, expected_size in cases:
            with self.subTest(size=original_size):
                # Real Pillow resizing; only file access and the Tk bridge are mocked.
                with Image.new("RGB", original_size) as source:
                    with patch("main.filedialog.askopenfilename", return_value="drawing.png"), \
                            patch("main.Image.open", return_value=source), \
                            patch("main.ImageTk.PhotoImage") as photo:
                        self.app.import_image()
                        converted_image = photo.call_args.args[0]
                        self.assertEqual(converted_image.size, expected_size)
                        self.canvas.create_image.assert_called_with(
                            400, 300, image=photo.return_value
                        )
                        self.assertIs(self.app._image_refs[-1], photo.return_value)
                        self.assertEqual(self.app.items[-1], self.canvas.create_image.return_value)
                        if converted_image is not source:
                            converted_image.close()

    @patch("main.ImageTk.PhotoImage")
    @patch("main.Image.open")
    @patch("main.filedialog.askopenfilename", return_value="drawing.png")
    def test_imported_image_can_be_undone(self, dialog, open_image, photo):
        open_image.return_value.size = (100, 50)
        self.canvas.create_image.return_value = 21
        self.app.import_image()
        self.app.undo()
        self.canvas.delete.assert_called_once_with(21)
        self.assertEqual(self.app.items, [])

    @patch("main.Image.open")
    @patch("main.filedialog.asksaveasfilename", return_value="")
    def test_cancel_save_does_not_export_or_show_success(self, dialog, open_image):
        self.app.save_draw()
        self.canvas.create_rectangle.assert_not_called()
        self.canvas.postscript.assert_not_called()
        open_image.assert_not_called()
        self.showinfo.assert_not_called()

    def prepare_save(self, filename="drawing.png"):
        replacements = {
            "main.filedialog.asksaveasfilename": {"return_value": filename},
            "main.datetime": {},
            "main.Image.open": {},
            "main.os.path.exists": {"return_value": True},
            "main.os.remove": {},
        }
        mocks = {}
        for target, kwargs in replacements.items():
            patcher = patch(target, **kwargs)
            mocks[target] = patcher.start()
            self.addCleanup(patcher.stop)
        mocks["main.datetime"].now.return_value = datetime(2026, 1, 2, 3, 4, 5)
        self.canvas.create_rectangle.return_value = 99
        self.app.items = [11]
        return mocks["main.Image.open"], mocks["main.os.remove"]

    def test_save_exports_selected_format_and_cleans_temporary_artifacts(self):
        for extension in ("png", "jpg"):
            with self.subTest(extension=extension):
                filename = os.path.join("drawings", "example." + extension)
                open_image, remove = self.prepare_save(filename)
                self.app.save_draw()
                ps_path = os.path.join("drawings", "DrawingBoard_20260102_030405.ps")
                self.canvas.postscript.assert_called_with(file=ps_path, colormode="color")
                open_image.assert_called_once_with(ps_path)
                open_image.return_value.save.assert_called_once_with(filename)
                open_image.return_value.close.assert_called_once()
                remove.assert_called_once_with(ps_path)
                self.canvas.delete.assert_called_with(99)
                self.assertEqual(self.app.items, [11])
                self.canvas.create_rectangle.assert_called_with(
                    0, 0, 800, 600, fill=WHITE, outline=""
                )
                self.canvas.tag_lower.assert_called_with(99)
                self.showinfo.assert_called_with(
                    "Drawing Board info", "Image saved successfully as example." + extension
                )

    def test_failed_conversion_cleans_up_and_reports_only_error(self):
        open_image, remove = self.prepare_save()
        open_image.side_effect = OSError("conversion failed")
        self.app.save_draw()
        remove.assert_called_once_with(os.path.join(".", "DrawingBoard_20260102_030405.ps"))
        self.canvas.delete.assert_called_once_with(99)
        self.assertEqual(self.app.items, [11])
        self.showinfo.assert_called_once_with(
            "Drawing Board error", "Cannot save image drawing.png: conversion failed"
        )

    def test_failed_image_write_closes_image_and_cleans_up(self):
        open_image, remove = self.prepare_save()
        open_image.return_value.save.side_effect = OSError("disk full")
        self.app.save_draw()
        open_image.return_value.close.assert_called_once()
        remove.assert_called_once()
        self.canvas.delete.assert_called_once_with(99)
        self.showinfo.assert_called_once_with(
            "Drawing Board error", "Cannot save image drawing.png: disk full"
        )

    def test_failed_postscript_export_still_removes_background(self):
        open_image, remove = self.prepare_save()
        self.canvas.postscript.side_effect = OSError("export failed")
        self.app.save_draw()
        open_image.assert_not_called()
        self.canvas.delete.assert_called_once_with(99)
        self.assertEqual(self.app.items, [11])
        self.showinfo.assert_called_once_with(
            "Drawing Board error", "Cannot save image drawing.png: export failed"
        )


if __name__ == "__main__":
    unittest.main()
