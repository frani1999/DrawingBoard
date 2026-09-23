"""Canvas figure editing and transactional undo integration."""

from dataclasses import replace
from math import hypot
import tkinter as tk
from tkinter import ttk

from figures import Figure, KINDS


class FigureTool:
    def __init__(self, app):
        self.app = app
        self.canvas = app.canvas
        self.figures = {}  # Stable canvas ID -> immutable model.
        self.selected = None
        self.kind = None
        self.gesture = None
        self.preview = None
        self.decorations = []
        self.dialog = None

    def show_chooser(self, event=None):
        self.app.stop_drawing()
        if self.dialog is not None and self.dialog.winfo_exists():
            self.dialog.lift()
            self.dialog.focus_set()
            return 'break'
        self.dialog = dialog = tk.Toplevel(self.app.window)
        dialog.title('Figures')
        dialog.transient(self.app.window)
        dialog.iconphoto(False, self.app._logo)
        dialog.resizable(False, False)
        body = ttk.Frame(dialog, padding=20)
        body.pack(fill='both', expand=True)
        ttk.Label(body, text='Choose an outlined figure, then drag on the board.').pack(pady=(0, 12))
        for kind in KINDS:
            ttk.Button(body, text=kind,
                       command=lambda kind=kind: self.choose(kind)).pack(fill='x', pady=3)
        ttk.Button(body, text='Edit existing figures',
                   command=lambda: self.choose(None)).pack(fill='x', pady=(12, 3))
        cancel = ttk.Button(body, text='Cancel', command=self.close_chooser)
        cancel.pack(fill='x', pady=3)
        dialog.protocol('WM_DELETE_WINDOW', self.close_chooser)
        dialog.bind('<Escape>', self.close_chooser)
        cancel.focus_set()
        return 'break'

    def close_chooser(self, event=None):
        if self.dialog is not None:
            self.dialog.destroy()
            self.dialog = None
            self.canvas.focus_set()
        return 'break'

    def choose(self, kind):
        self.app._select_tool('figure')
        self.kind = kind
        self.close_chooser()

    def color(self, figure):
        if figure.custom_color:
            return figure.color
        return 'white' if self.app.background_color == 'black' else 'black'

    def render(self, item, figure):
        self.canvas.coords(item, *[v for p in figure.points() for v in p])
        self.canvas.itemconfigure(item, fill=self.color(figure), width=figure.border)

    def create(self, figure, preview=False):
        return self.canvas.create_line(
            *[v for p in figure.points() for v in p],
            fill=self.color(figure), width=figure.border,
            joinstyle='round', capstyle='round',
            tags=('figure_preview',) if preview else ('figure',))

    def clear_decorations(self):
        for item in self.decorations:
            self.canvas.delete(item)
        self.decorations.clear()

    def show_selection(self):
        self.clear_decorations()
        if self.app.active_tool != 'figure' or self.selected not in self.figures:
            return
        figure = self.figures[self.selected]
        if self.canvas.itemcget(self.selected, 'state') == 'hidden':
            return
        corners = figure.corners()
        points = corners + corners[:1]
        self.decorations.append(self.canvas.create_line(
            *[v for p in points for v in p], fill='#2474c7', dash=(4, 3),
            tags=('figure_decoration',)))
        top = figure.world(0, -figure.height / 2)
        handle = figure.rotation_handle()
        self.decorations.append(self.canvas.create_line(
            *top, *handle, fill='#2474c7', tags=('figure_decoration',)))
        for x, y in corners:
            self.decorations.append(self.canvas.create_rectangle(
                x - 5, y - 5, x + 5, y + 5, fill='white', outline='#2474c7',
                tags=('figure_decoration',)))
        x, y = handle
        self.decorations.append(self.canvas.create_oval(
            x - 6, y - 6, x + 6, y + 6, fill='#2474c7', outline='white',
            tags=('figure_decoration',)))

    def start(self, event):
        self.cancel()
        point = (event.x, event.y)
        self.canvas.focus_set()
        if (self.selected in self.figures and
                self.canvas.itemcget(self.selected, 'state') != 'hidden'):
            figure = self.figures[self.selected]
            handles = figure.corners() + [figure.rotation_handle()]
            for index, (x, y) in enumerate(handles):
                if hypot(event.x - x, event.y - y) <= 9:
                    self.gesture = dict(mode='resize' if index < 4 else 'rotate',
                                        corner=index, start=point, before=figure)
                    return
        self.selected = None
        for item in reversed(self.canvas.find_all()):
            if (item in self.figures and
                    self.canvas.itemcget(item, 'state') != 'hidden' and
                    self.figures[item].hit(*point)):
                self.selected = item
                break
        self.show_selection()
        if self.selected is None and self.kind is not None:
            self.gesture = dict(mode='create', start=point, before=None,
                                border=self.app.pencil_size,
                                color=self.app.line_color,
                                custom_color=self.app._custom_color)

    def move(self, event):
        if self.gesture is None:
            return
        g = self.gesture
        point = (event.x, event.y)
        if g['mode'] == 'create':
            figure = Figure.from_drag(self.kind, g['start'], point,
                                      g['border'], g['color'], g['custom_color'])
            if figure is None:
                if self.preview is not None:
                    self.canvas.delete(self.preview)
                    self.preview = None
            elif self.preview is None:
                self.preview = self.create(figure, preview=True)
            else:
                self.render(self.preview, figure)
            g['after'] = figure
        else:
            before = g['before']
            if g['mode'] == 'resize':
                # Preserve the initial pointer-to-handle offset. Clicking near
                # a handle (including rounded screen coordinates) must not jump.
                x, y = before.corners()[g['corner']]
                point = (x + point[0] - g['start'][0],
                         y + point[1] - g['start'][1])
                figure = before.resized(g['corner'], point)
            else:
                figure = before.rotated(g['start'], point)
            self.figures[self.selected] = figure
            self.render(self.selected, figure)
            self.show_selection()

    def finish(self, event):
        if self.gesture is None:
            return
        self.move(event)
        g, self.gesture = self.gesture, None
        if g['mode'] == 'create':
            figure = g.get('after')
            if self.preview is not None:
                self.canvas.delete(self.preview)
                self.preview = None
            if figure is not None:
                item = self.create(figure)
                self.figures[item] = figure
                self.selected = item
                self.app.items.append(dict(type='figure_create', item=item))
        else:
            self.record_update(g['before'])
        self.show_selection()

    def record_update(self, before):
        after = self.figures[self.selected]
        if after != before:
            self.app.items.append(dict(type='figure_update', item=self.selected,
                                       before=before, after=after))

    def cancel(self, event=None):
        if self.gesture is not None:
            before = self.gesture['before']
            if before is not None and self.selected in self.figures:
                self.figures[self.selected] = before
                self.render(self.selected, before)
            self.gesture = None
        if self.preview is not None:
            self.canvas.delete(self.preview)
            self.preview = None
        self.show_selection()
        return 'break'

    def change_width(self, record=True):
        if self.app.active_tool == 'figure' and self.selected in self.figures:
            before = self.figures[self.selected]
            self.figures[self.selected] = replace(before, border=self.app.pencil_size)
            self.render(self.selected, self.figures[self.selected])
            if record:
                self.record_update(before)
            self.show_selection()

    def undo(self, action):
        item = action['item']
        if action['type'] == 'figure_create':
            self.canvas.delete(item)
            del self.figures[item]
            if self.selected == item:
                self.selected = None
        else:
            self.figures[item] = action['before']
            self.render(item, action['before'])
        self.show_selection()

    def recolor(self):
        for item, figure in self.figures.items():
            self.render(item, figure)
        self.show_selection()
