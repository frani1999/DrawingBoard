"""Toolbar mapping and widget interaction without a graphical desktop."""

from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from toolbar import Toolbar, size_from_percent, size_percent


class ToolbarTests(unittest.TestCase):
    def setUp(self):
        for target in ('toolbar.tk.Canvas', 'toolbar.ttk.Frame', 'toolbar.ttk.Label'):
            patcher = patch(target)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.app = Mock(pencil_size=1, line_color='black', _thickness_gesture=None)
        with patch('toolbar.tk.Canvas') as canvas:
            self.swatch, self.track = Mock(), Mock()
            self.track.winfo_width.return_value = 220
            canvas.side_effect = [self.swatch, self.track]
            self.toolbar = Toolbar(self.app, 1, 50)

    def test_mapping_clamps_rounds_and_reaches_every_pixel_size(self):
        for percent, size in ((-20, 1), (0, 1), (50, 26), (100, 50), (130, 50)):
            self.assertEqual(size_from_percent(percent, 1, 50), size)
        self.assertEqual(size_percent(25, 1, 50), 49)
        self.assertEqual(size_percent(26, 1, 50), 51)
        for size in range(1, 51):
            self.assertEqual(size_from_percent(100 * (size - 1) / 49, 1, 50), size)

    def test_initial_layout_swatch_activation_and_separate_canvas(self):
        self.toolbar.frame.pack.assert_called_once_with(before=self.app.canvas, fill='x')
        self.assertIsNot(self.track, self.app.canvas)
        self.swatch.configure.assert_called_with(background='black')
        self.toolbar.label.configure.assert_called_with(text='0%')
        bindings = dict(call.args for call in self.swatch.bind.call_args_list)
        for key in ('<Button-1>', '<Return>', '<space>'):
            self.assertEqual(bindings[key], self.app.select_color)

    def test_refresh_moves_thumb_without_mutating_application(self):
        self.app.pencil_size = 50
        self.app.line_color = 'white'
        self.toolbar.refresh()
        self.toolbar.label.configure.assert_called_with(text='100%')
        self.swatch.configure.assert_called_with(background='white')
        self.track.coords.assert_any_call('thumb', 205, 3, 211, 25)
        self.app._set_size.assert_not_called()

    def test_drag_clamps_outside_release_and_ignores_motion_after_cancel(self):
        self.app._begin_thickness.side_effect = lambda: setattr(self.app, '_thickness_gesture', {})
        self.toolbar.start(SimpleNamespace(x=12))
        self.app._set_size.assert_called_with(1, record=False)
        self.toolbar.finish(SimpleNamespace(x=900))
        self.app._set_size.assert_called_with(50, record=False)
        self.app._finish_thickness.assert_called_once()
        self.app.canvas.focus_set.assert_called_once()
        self.app._thickness_gesture = None
        self.app._set_size.reset_mock()
        self.toolbar.move(SimpleNamespace(x=50))
        self.app._set_size.assert_not_called()

    def test_focus_loss_cancels_and_arrow_keys_use_shared_size_path(self):
        bindings = dict(call.args for call in self.track.bind.call_args_list)
        self.assertEqual(bindings['<FocusOut>'], self.app._cancel_thickness)
        bindings['<Left>'](None)
        self.app._change_size.assert_called_with(-1)
        bindings['<Right>'](None)
        self.app._change_size.assert_called_with(1)
