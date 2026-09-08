"""Test application behavior without a display, dialogs, or Ghostscript."""

import os
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import call, patch

from PIL import Image

from main import BLACK, WHITE, DrawingBoardApp


class DrawingBoardTests(unittest.TestCase):
    def setUp(self):
        # Exercise the real constructor while keeping all Tk widgets headless.
        for target in ("main.tk.Tk", "main.tk.Canvas", "main.tk.Menu"):
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
            call(10, 20, 30, 40, fill=BLACK),
            call(30, 40, 50, 60, fill=BLACK),
        ])
        self.assertEqual(self.app.items, [11, 12])
        self.assertEqual((self.app.last_x, self.app.last_y), (50, 60))

        self.app.undo()
        self.canvas.delete.assert_called_once_with(12)
        self.assertEqual(self.app.items, [11])

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
        self.canvas.find_all.return_value = [11, 12]
        self.canvas.type.side_effect = lambda item: "line" if item == 11 else "image"
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
        self.canvas.create_line.assert_called_once_with(1, 2, 3, 4, fill=WHITE)

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
