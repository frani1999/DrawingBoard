"""Real geometry and stateful canvas tests for the rubber tool."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from eraser import remaining_segments
from main import DrawingBoardApp, MAX_PENCIL_SIZE, MIN_PENCIL_SIZE


class EraserGeometryTests(unittest.TestCase):
    def test_click_splits_line_and_preserves_untouched_ends(self):
        self.assertEqual(remaining_segments((0, 0, 100, 0), (50, 0), (50, 0), 10),
                         [(0, 0, 40, 0), (60, 0, 100, 0)])

    def test_fast_drag_erases_between_events(self):
        self.assertEqual(remaining_segments((0, 0, 100, 0), (50, -100), (50, 100), 10),
                         [(0, 0, 40, 0), (60, 0, 100, 0)])

    def test_parallel_drag_and_full_erasure(self):
        self.assertEqual(remaining_segments((0, 0, 100, 0), (20, 0), (80, 0), 10),
                         [(0, 0, 10, 0), (90, 0, 100, 0)])
        self.assertEqual(remaining_segments((20, 0, 80, 0), (0, 0), (100, 0), 10), [])

    def test_miss_tangent_and_zero_length_marks(self):
        line = (0, 0, 100, 0)
        self.assertEqual(remaining_segments(line, (50, 20), (50, 20), 10), [line])
        self.assertEqual(remaining_segments(line, (50, 10), (50, 10), 10), [line])
        self.assertEqual(remaining_segments((5, 5, 5, 5), (5, 5), (5, 5), 1), [])

    def test_diagonal_drag_intersects_line(self):
        pieces = remaining_segments((0, 50, 100, 50), (0, 0), (100, 100), 10)
        self.assertEqual(len(pieces), 2)
        self.assertAlmostEqual(pieces[0][2], 50 - 10 * 2 ** 0.5)
        self.assertAlmostEqual(pieces[1][0], 50 + 10 * 2 ** 0.5)


class RubberTests(unittest.TestCase):
    def setUp(self):
        for name in ('tk.Tk', 'tk.Menu', 'tk.Canvas', 'ImageTk.PhotoImage'):
            patcher = patch('main.' + name)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.app = DrawingBoardApp()
        self.canvas = self.app.canvas
        self.records = {}
        self.next_id = 10

        def create_line(*coords, **options):
            self.next_id += 1
            self.records[self.next_id] = dict(coords=tuple(coords), type='line',
                                              state='normal', tags=())
            self.records[self.next_id].update(options)
            return self.next_id

        def configure(item, **options):
            if item in self.records:
                self.records[item].update(options)

        self.canvas.create_line.side_effect = create_line
        self.canvas.coords.side_effect = lambda item, *args: self.records[item]['coords'] if item in self.records else ()
        self.canvas.type.side_effect = lambda item: self.records[item]['type']
        self.canvas.itemcget.side_effect = lambda item, key: self.records[item][key]
        self.canvas.gettags.side_effect = lambda item: self.records[item]['tags']
        self.canvas.itemconfigure.side_effect = configure
        self.canvas.itemconfig.side_effect = configure
        self.canvas.delete.side_effect = lambda item: self.records.pop(item, None)
        self.canvas.addtag_withtag.side_effect = lambda tag, item: self.records[item].update(tags=(tag,))
        self.canvas.find_withtag.side_effect = lambda tag: [i for i, r in self.records.items() if tag in r['tags']]
        self.canvas.find_overlapping.side_effect = lambda *args: [i for i, r in self.records.items() if r['state'] != 'hidden']

    def line(self, color=None):
        self.app._custom_color = color is not None
        self.app.line_color = color or 'black'
        self.app.start_drawing(SimpleNamespace(x=0, y=50))
        self.app.draw(SimpleNamespace(x=100, y=50))
        self.app.stop_drawing()
        return self.app.items[-1]

    def visible_lines(self):
        return [r for r in self.records.values() if r['type'] == 'line' and r['state'] == 'normal']

    @patch('main.askokcancel', return_value=True)
    def test_undo_all_removes_nested_rubber_cuts_and_dots_preserving_image(self, confirm):
        self.records[500] = dict(type='image', state='normal', tags=())
        self.app.items.append(500)
        self.line()
        self.records[501] = dict(type='oval', state='normal', tags=('pencil_dot',),
                                 coords=(45, 45, 55, 55), fill='red')
        self.app.items.append(501)
        self.app.select_rubber()
        self.app.start_drawing(SimpleNamespace(x=50, y=50))
        self.app.stop_drawing()
        self.app.start_drawing(SimpleNamespace(x=25, y=50))
        self.app.undo_all()
        self.assertEqual(self.records, {500: dict(type='image', state='normal', tags=())})
        self.assertEqual(self.app.items, [500])
        self.app.select_pencil()
        self.line()
        self.assertEqual(len(self.visible_lines()), 1)
        self.app.undo()
        self.assertEqual(list(self.records), [500])

    def test_shortcuts_and_menu_entries(self):
        import main
        bindings = dict(c.args for c in self.app.window.bind.call_args_list)
        for key, callback, label in (('C', self.app.select_color, 'Color'),
                                     ('R', self.app.select_rubber, 'Rubber'),
                                     ('P', self.app.select_pencil, 'Pencil')):
            self.assertEqual(bindings[f'<Control-Shift-{key}>'], callback)
            main.tk.Menu.return_value.add_command.assert_any_call(
                label=label, accelerator=f'Ctrl+Shift+{key}', command=callback)

    def test_switching_tools_migrates_size_and_preserves_color(self):
        self.app.line_color = '#ff0000'
        self.app.increase_pencil_size()
        self.assertEqual(self.app.select_rubber(), 'break')
        self.assertEqual(self.app.pencil_size, 2)
        self.canvas.configure.assert_called_with(cursor='none')
        self.app.increase_pencil_size()
        self.app.select_pencil()
        self.assertEqual(self.app.pencil_size, 3)
        self.assertEqual(self.app.line_color, '#ff0000')
        self.canvas.configure.assert_called_with(cursor='pencil')
        self.app.select_rubber()
        for _ in range(60):
            self.app.increase_pencil_size()
        self.assertEqual(self.app.pencil_size, MAX_PENCIL_SIZE)
        for _ in range(60):
            self.app.decrease_pencil_size()
        self.assertEqual(self.app.pencil_size, MIN_PENCIL_SIZE)

    def test_rubber_drag_cuts_marks_preserves_images_and_can_be_undone(self):
        original = self.line('#ff0000')
        self.records[500] = dict(type='image', state='normal', tags=())
        self.app.pencil_size = 10
        self.app.select_rubber()
        self.app.start_drawing(SimpleNamespace(x=50, y=0))
        self.app.draw(SimpleNamespace(x=50, y=100))
        self.app.stop_drawing()
        visible = self.visible_lines()
        self.assertEqual(len(visible), 2)
        self.assertEqual(visible[0]['coords'], (0, 50, 44.5, 50))
        for actual, expected in zip(visible[1]['coords'], (55.5, 50, 100, 50)):
            self.assertAlmostEqual(actual, expected)
        self.assertTrue(all(r['fill'] == '#ff0000' for r in visible))
        self.assertEqual(self.records[500]['state'], 'normal')
        self.app.undo()
        self.assertEqual(self.visible_lines(), [self.records[original]])
        self.app.undo()
        self.assertEqual(self.visible_lines(), [])

    def test_click_erases_and_multiple_motions_undo_as_one_action(self):
        original = self.line()
        self.app.pencil_size = 10
        self.app.select_rubber()
        self.app.start_drawing(SimpleNamespace(x=25, y=50))
        self.assertEqual(len(self.visible_lines()), 2)
        self.app.draw(SimpleNamespace(x=75, y=50))
        self.app.stop_drawing()
        self.assertEqual(len(self.app.items), 2)
        self.app.switch_theme()
        self.app.undo()
        self.assertEqual(self.visible_lines(), [self.records[original]])
        self.assertEqual(self.records[original]['fill'], 'white')

    def test_rubber_erases_dot_and_undo_restores_it(self):
        self.records[501] = dict(type='oval', state='normal', tags=('pencil_dot',),
                                 coords=(45, 45, 55, 55), fill='red')
        self.records[502] = dict(type='oval', state='normal', tags=(),
                                 coords=(45, 45, 55, 55))
        self.app.items.append(501)
        self.app.select_rubber()
        self.app.start_drawing(SimpleNamespace(x=50, y=0))
        self.assertEqual(self.records[501]['state'], 'normal')
        self.app.draw(SimpleNamespace(x=50, y=100))
        self.app.stop_drawing()
        self.assertEqual(self.records[501]['state'], 'hidden')
        self.assertEqual(self.records[502]['state'], 'normal')
        self.app.undo()
        self.assertEqual(self.records[501]['state'], 'normal')

    def test_empty_erasure_and_motion_without_press_do_nothing(self):
        self.app.select_rubber()
        self.app.draw(SimpleNamespace(x=1, y=1))
        self.canvas.find_overlapping.assert_not_called()
        self.app.start_drawing(SimpleNamespace(x=1, y=1))
        self.app.stop_drawing()
        self.assertEqual(self.app.items, [])

    def test_separate_rubber_strokes_undo_in_reverse_order(self):
        original = self.line()
        self.app.pencil_size = 10
        self.app.select_rubber()
        self.app.start_drawing(SimpleNamespace(x=25, y=50))
        self.app.stop_drawing()
        first_cut = [r.copy() for r in self.visible_lines()]
        self.app.start_drawing(SimpleNamespace(x=75, y=50))
        self.app.stop_drawing()
        self.assertEqual(len(self.visible_lines()), 3)
        self.app.undo()
        self.assertEqual(self.visible_lines(), first_cut)
        self.app.undo()
        self.assertEqual(self.visible_lines(), [self.records[original]])

    def test_rubber_icon_outline_and_leave(self):
        self.app.select_rubber()
        self.app.pencil_size = 20
        self.app._move_cursor(SimpleNamespace(x=50, y=50))
        self.canvas.coords.assert_any_call(self.app._cursor_outline, 40, 40, 60, 60)
        for item in (self.app._rubber_icon, self.app._rubber_sleeve):
            self.canvas.itemconfigure.assert_any_call(item, state='normal')
        self.app._hide_cursor()
        for item in (self.app._rubber_icon, self.app._rubber_sleeve):
            self.canvas.itemconfigure.assert_any_call(item, state='hidden')


if __name__ == '__main__':
    unittest.main()
