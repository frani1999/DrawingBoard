"""Figure geometry and editing with a stateful canvas (no display required)."""

from dataclasses import replace
from math import cos, radians, sin
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from figures import Figure, KINDS
from main import DrawingBoardApp


def event(x, y):
    return SimpleNamespace(x=x, y=y)


class GeometryTests(unittest.TestCase):
    def test_catalog_closed_paths_and_border_hits(self):
        for kind in KINDS:
            with self.subTest(kind=kind):
                figure = Figure(kind, 100, 100, 120, 80)
                self.assertEqual(figure.points()[0], figure.points()[-1])
                self.assertTrue(figure.hit(*figure.points()[0]))
                self.assertFalse(figure.hit(100, 100))
                self.assertFalse(figure.hit(500, 500))

    def test_drag_normalizes_all_directions_and_rejects_degenerate(self):
        for start, end in (((0, 0), (100, 80)), ((100, 80), (0, 0)),
                           ((100, 0), (0, 80)), ((0, 80), (100, 0))):
            self.assertEqual(Figure.from_drag('Rectangle', start, end, 4, 'red', True),
                             Figure('Rectangle', 50, 40, 100, 80, 4, 'red', True))
        for end in ((0, 0), (0, 40), (40, 0)):
            self.assertIsNone(Figure.from_drag('Ellipse', (0, 0), end, 1, 'black', False))

    def test_rotation_and_inverse_transform(self):
        figure = Figure('Ellipse', 100, 100, 120, 50)
        for angle in (0, 90, 37, 360):
            with self.subTest(angle=angle):
                rotated = figure.rotated((200, 100), (
                    100 + 100 * cos(radians(angle)), 100 + 100 * sin(radians(angle))))
                self.assertAlmostEqual(rotated.angle, angle % 360)
                x, y = rotated.local(*rotated.world(14, -28))
                self.assertAlmostEqual(x, 14)
                self.assertAlmostEqual(y, -28)
        self.assertEqual(figure.rotated((200, 100), (100, 100)), figure)
        self.assertNotEqual(figure.points(), replace(figure, angle=37).points())

    def test_rotated_resize_preserves_center_angle_border_and_clamps(self):
        figure = Figure('Triangle', 120, 90, 100, 80, 12, angle=37)
        resized = figure.resized(2, figure.world(80, 25))
        self.assertAlmostEqual(resized.width, 160)
        self.assertAlmostEqual(resized.height, 50)
        self.assertEqual((resized.cx, resized.cy, resized.angle, resized.border),
                         (120, 90, 37, 12))
        clamped = figure.resized(2, figure.world(-40, -30))
        self.assertEqual((clamped.width, clamped.height), (1, 1))
        for _ in range(100):
            figure = figure.resized(2, figure.world(80, 25))
        self.assertAlmostEqual(figure.width, 160)
        self.assertAlmostEqual(figure.height, 50)


class FigureTests(unittest.TestCase):
    def setUp(self):
        self.mocks = {}
        for name in ('tk.Tk', 'tk.Menu', 'tk.Canvas', 'tk.Toplevel',
                     'ImageTk.PhotoImage', 'ttk.Frame', 'ttk.Label',
                     'ttk.Button', 'ttk.Scrollbar', 'tkfont.nametofont', 'showinfo'):
            patcher = patch('main.' + name)
            self.mocks[name] = patcher.start()
            self.addCleanup(patcher.stop)
        self.canvas = self.mocks['tk.Canvas'].return_value
        self.records = {}
        self.order = []
        self.next_id = 0

        def create(kind, coords, options):
            self.next_id += 1
            self.records[self.next_id] = dict(type=kind, coords=tuple(coords),
                                               state='normal', tags=())
            self.records[self.next_id].update(options)
            self.order.append(self.next_id)
            return self.next_id

        for kind in ('line', 'oval', 'rectangle', 'polygon', 'image'):
            getattr(self.canvas, 'create_' + kind).side_effect = (
                lambda *coords, kind=kind, **options: create(kind, coords, options))

        def coords(item, *values):
            if values:
                self.records[item]['coords'] = tuple(values)
            return self.records[item]['coords']

        def configure(item, **options):
            self.records[item].update(options)

        def delete(item):
            self.records.pop(item, None)
            if item in self.order:
                self.order.remove(item)

        def raise_item(item):
            self.order.remove(item)
            self.order.append(item)

        def lower(item, below=None):
            self.order.remove(item)
            self.order.insert(self.order.index(below) if below else 0, item)

        self.canvas.coords.side_effect = coords
        self.canvas.itemconfigure.side_effect = configure
        self.canvas.itemconfig.side_effect = configure
        self.canvas.delete.side_effect = delete
        self.canvas.type.side_effect = lambda item: self.records[item]['type']
        self.canvas.itemcget.side_effect = lambda item, key: self.records[item].get(key, '')
        self.canvas.gettags.side_effect = lambda item: self.records[item]['tags']
        self.canvas.find_all.side_effect = lambda: tuple(self.order)
        self.canvas.find_withtag.side_effect = lambda tag: tuple(
            i for i in self.order if tag in self.records[i]['tags'])
        self.canvas.find_overlapping.side_effect = lambda *args: tuple(
            i for i in self.order if self.records[i]['state'] != 'hidden')
        self.canvas.addtag_withtag.side_effect = lambda tag, item: self.records[item].update(
            tags=self.records[item]['tags'] + (tag,))
        self.canvas.tag_raise.side_effect = raise_item
        self.canvas.tag_lower.side_effect = lower
        self.canvas.winfo_width.return_value = 800
        self.canvas.winfo_height.return_value = 600
        self.app = DrawingBoardApp()
        self.tool = self.app.figure_tool

    def place(self, kind='Rectangle', start=(100, 100), end=(300, 200)):
        self.tool.choose(kind)
        self.app.start_drawing(event(*start))
        self.app.draw(event(*end))
        self.app.stop_drawing(event(*end))
        return self.tool.selected

    def test_each_kind_commits_one_action_with_current_style(self):
        self.app.select_rubber()
        self.app.increase_pencil_size()
        self.app.line_color, self.app._custom_color = '#abcdef', True
        for index, kind in enumerate(KINDS):
            item = self.place(kind, (100 + index * 220, 100), (300 + index * 220, 200))
            self.assertEqual(self.records[item]['width'], 2)
            self.assertEqual(self.records[item]['fill'], '#abcdef')
            self.assertEqual(self.app.items[-1], dict(type='figure_create', item=item))
            self.assertFalse(self.canvas.find_withtag('figure_preview'))
        self.assertEqual(len(self.app.items), 3)

    def test_zero_area_stationary_and_escape_placement_leave_no_history(self):
        self.tool.choose('Rectangle')
        for end in ((100, 100), (100, 140), (150, 100)):
            self.app.start_drawing(event(100, 100))
            self.app.draw(event(150, 140))
            self.app.stop_drawing(event(*end))
            self.assertEqual(self.app.items, [])
        self.app.start_drawing(event(100, 100))
        self.app.draw(event(150, 140))
        self.tool.cancel()
        self.app.stop_drawing(event(150, 140))
        self.assertEqual(self.app.items, [])
        self.assertIsNone(self.tool.preview)

    def test_resize_rotates_and_undo_restores_same_item_and_stacking(self):
        item = self.place('Ellipse')
        before = self.tool.figures[item]
        handle = before.rotation_handle()
        self.app.start_drawing(event(*handle))
        for point in ((300, 100), (300, 150)):
            self.app.draw(event(*point))
        self.app.stop_drawing(event(300, 150))
        rotated = self.tool.figures[item]
        self.assertAlmostEqual(rotated.angle, 90)
        self.assertEqual(len(self.app.items), 2)
        self.app.start_drawing(event(*rotated.corners()[2]))
        self.app.stop_drawing(event(*rotated.world(140, 70)))
        self.assertAlmostEqual(self.tool.figures[item].width, 280)
        self.assertAlmostEqual(self.tool.figures[item].height, 140)
        self.app.undo()
        self.assertEqual(self.tool.figures[item], rotated)
        self.app.undo()
        self.assertEqual(self.tool.figures[item], before)
        self.app.undo()
        self.assertNotIn(item, self.records)
        self.assertIsNone(self.tool.selected)
        self.assertFalse(self.tool.decorations)

    def test_escape_switch_and_dialog_cancel_transform_without_history(self):
        item = self.place()
        before = self.tool.figures[item]
        for cancel in (self.tool.cancel, self.app.select_pencil, self.app.select_figures):
            self.tool.choose(None)
            self.app.start_drawing(event(200, 100))
            self.app.start_drawing(event(*before.corners()[2]))
            self.app.draw(event(400, 300))
            cancel()
            self.assertEqual(self.tool.figures[item], before)
            self.assertEqual(len(self.app.items), 1)
            self.tool.close_chooser()

    def test_noop_transform_and_selection_do_not_add_history(self):
        item = self.place()
        figure = self.tool.figures[item]
        for point in (figure.corners()[2], figure.rotation_handle()):
            self.app.start_drawing(event(*point))
            self.app.stop_drawing(event(*point))
        self.assertEqual(len(self.app.items), 1)

    def test_click_near_rotated_handle_does_not_jump_or_add_undo(self):
        item = self.place()
        self.tool.figures[item] = figure = replace(self.tool.figures[item], angle=37)
        self.tool.render(item, figure)
        self.tool.show_selection()
        x, y = figure.corners()[2]
        point = event(round(x) + 3, round(y) - 2)
        self.app.start_drawing(point)
        self.app.stop_drawing(point)
        self.assertEqual(self.tool.figures[item], figure)
        self.assertEqual(len(self.app.items), 1)

    @patch('main.Image.open')
    @patch('main.filedialog.askopenfilename', return_value='example.png')
    def test_import_keeps_figure_handles_above_new_image(self, dialog, image_open):
        self.place()
        image_open.return_value.size = (100, 100)
        self.app.import_image()
        image = self.app.items[-1]
        self.assertEqual(self.records[image]['type'], 'image')
        self.assertTrue(all(self.order.index(handle) > self.order.index(image)
                            for handle in self.tool.decorations))

    def test_topmost_border_selection_ignores_hidden_and_nonfigures(self):
        lower = self.place()
        upper = self.place('Triangle', (150, 120), (250, 200))
        self.tool.choose(None)
        # Both paths touch the bottom middle of their bounds.
        self.app.start_drawing(event(200, 200))
        self.assertEqual(self.tool.selected, upper)
        self.canvas.itemconfigure(upper, state='hidden')
        self.tool.selected = None
        self.app.start_drawing(event(200, 200))
        self.assertEqual(self.tool.selected, lower)
        self.app.start_drawing(event(500, 400))
        self.app.stop_drawing(event(700, 500))
        self.assertIsNone(self.tool.selected)
        self.assertEqual(len(self.app.items), 2)

    def test_size_limits_selected_border_undo_and_other_tools(self):
        item = self.place()
        self.app.increase_pencil_size()
        self.assertEqual(self.tool.figures[item].border, 2)
        self.app.undo()
        self.assertEqual(self.tool.figures[item].border, 1)
        self.assertEqual(self.app.pencil_size, 2)
        self.app.pencil_size = 50
        history = list(self.app.items)
        self.app.increase_pencil_size()
        self.assertEqual(self.app.items, history)
        self.app.select_rubber()
        self.app.decrease_pencil_size()
        self.assertEqual(self.tool.figures[item].border, 1)
        self.assertEqual(self.app.pencil_size, 49)

    def test_theme_and_undo_use_color_policy_not_stale_color(self):
        default = self.place()
        self.app.increase_pencil_size()
        self.app.switch_theme()
        self.app.undo()
        self.assertEqual(self.records[default]['fill'], 'white')
        for color in ('black', 'white', '#abcdef'):
            self.app.line_color, self.app._custom_color = color, True
            custom = self.place('Ellipse', (400, 300), (500, 400))
            self.app.switch_theme()
            self.assertEqual(self.records[custom]['fill'], color)

    @patch('main.colorchooser.askcolor', return_value=(None, None))
    def test_cancel_color_keeps_figure_style_and_new_figure_defaults(self, chooser):
        item = self.place()
        before = self.tool.figures[item]
        self.app.select_color()
        self.assertEqual(self.tool.figures[item], before)
        self.assertFalse(self.app._custom_color)

    def test_rubber_ignores_figures_and_decorations_but_cuts_pencil(self):
        figure = self.place('Ellipse')
        figure_coords = self.records[figure]['coords']
        self.app.select_pencil()
        self.app.start_drawing(event(100, 150))
        self.app.draw(event(300, 150))
        self.app.stop_drawing()
        pencil = self.app.items[-1]
        self.app.select_rubber()
        self.app.start_drawing(event(200, 150))
        self.app.stop_drawing()
        self.assertEqual(self.records[figure]['coords'], figure_coords)
        self.assertEqual(self.records[figure]['state'], 'normal')
        self.assertEqual(self.records[pencil]['state'], 'hidden')
        self.app.undo()
        self.assertEqual(self.records[pencil]['state'], 'normal')
        self.assertLess(self.order.index(figure), self.order.index(pencil))

    def test_mixed_undo_all_preserves_imports_and_cancel_preserves_figures(self):
        image1 = self.canvas.create_image(10, 10)
        self.app.items.append(image1)
        figure = self.place()
        self.app.increase_pencil_size()
        image2 = self.canvas.create_image(20, 20)
        self.app.items.append(image2)
        refs = [object(), object()]
        self.app._image_refs = refs
        history = list(self.app.items)
        with patch('main.askokcancel', return_value=False):
            self.app.undo_all()
        self.assertEqual(self.app.items, history)
        self.assertIn(figure, self.tool.figures)
        with patch('main.askokcancel', return_value=True):
            self.app.undo_all()
            self.app.undo_all()
        self.assertEqual(self.app.items, [image1, image2])
        self.assertIs(self.app._image_refs, refs)
        self.assertEqual(self.tool.figures, {})
        self.app.undo()
        self.assertNotIn(image2, self.records)
        self.assertIn(image1, self.records)

    def test_chooser_reuse_cancel_menu_shortcut_and_pending_pencil(self):
        self.app.start_drawing(event(10, 10))
        self.app.select_figures()
        dialog = self.tool.dialog
        self.app.select_figures()
        dialog.lift.assert_called_once()
        self.mocks['tk.Menu'].return_value.add_command.assert_any_call(
            label='Figures', accelerator='Ctrl+Shift+F', command=self.app.select_figures)
        self.app.window.bind.assert_any_call('<Control-Shift-F>', self.app.select_figures)
        dialog.bind.assert_any_call('<Escape>', self.tool.close_chooser)
        dialog.protocol.assert_called_once_with('WM_DELETE_WINDOW', self.tool.close_chooser)
        self.tool.close_chooser()
        self.assertEqual(self.app.active_tool, 'pencil')
        self.assertEqual(self.app.items, [])
        self.canvas.focus_set.assert_called()

    def test_export_excludes_adornments_and_restores_after_all_failures(self):
        item = self.place('Ellipse')
        before = self.tool.figures[item]
        for failure in (None, 'postscript', 'conversion', 'save'):
            with self.subTest(failure=failure), patch(
                    'main.filedialog.asksaveasfilename', return_value='figure.png'), patch(
                    'main.Image.open') as image_open, patch('main.os.path.exists', return_value=True), patch(
                    'main.os.remove') as remove:
                image = image_open.return_value
                def export(**kwargs):
                    self.assertFalse(self.canvas.find_withtag('figure_decoration'))
                    self.assertFalse(self.canvas.find_withtag('figure_preview'))
                    self.assertEqual(self.records[item]['state'], 'normal')
                    for decoration in (self.app._cursor_outline, self.app._rubber_icon,
                                       self.app._rubber_sleeve):
                        self.assertEqual(self.records[decoration]['state'], 'hidden')
                    if failure == 'postscript':
                        raise OSError('postscript')
                self.canvas.postscript.side_effect = export
                if failure == 'conversion':
                    image_open.side_effect = OSError('conversion')
                if failure == 'save':
                    image.save.side_effect = OSError('save')
                self.app.save_draw()
                self.assertEqual(self.tool.figures[item], before)
                self.assertTrue(self.tool.decorations)
                self.assertEqual(len(self.app.items), 1)
                remove.assert_called_once()
                if failure in (None, 'save'):
                    image.close.assert_called_once()

    @patch('main.filedialog.asksaveasfilename', return_value='')
    def test_cancel_export_rolls_back_pending_edit_and_keeps_selection(self, dialog):
        item = self.place()
        before = self.tool.figures[item]
        self.app.start_drawing(event(*before.corners()[2]))
        self.app.draw(event(500, 300))
        self.app.save_draw()
        self.assertEqual(self.tool.figures[item], before)
        self.assertTrue(self.tool.decorations)
        self.canvas.postscript.assert_not_called()


if __name__ == '__main__':
    unittest.main()
