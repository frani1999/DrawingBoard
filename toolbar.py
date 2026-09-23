"""Color swatch and shared thickness control, separate from artwork."""

import tkinter as tk
from tkinter import ttk
from math import floor


def size_from_percent(percent, minimum, maximum):
    percent = max(0, min(100, percent))
    return minimum + floor(percent * (maximum - minimum) / 100 + 0.5)


def size_percent(size, minimum, maximum):
    return floor(100 * (size - minimum) / (maximum - minimum) + 0.5)


class Toolbar:
    def __init__(self, app, minimum, maximum):
        self.app = app
        self.minimum, self.maximum = minimum, maximum
        self.frame = ttk.Frame(app.window, padding=(12, 8))
        self.frame.pack(before=app.canvas, fill='x')
        ttk.Label(self.frame, text='Color').pack(side='left', padx=(0, 8))
        self.swatch = tk.Canvas(self.frame, width=26, height=26,
                                highlightthickness=2, highlightbackground='#777777',
                                highlightcolor='#2474c7', takefocus=True,
                                cursor='hand2')
        self.swatch.pack(side='left')
        for sequence in ('<Button-1>', '<Return>', '<space>'):
            self.swatch.bind(sequence, app.select_color)
        ttk.Label(self.frame, text='Thickness').pack(side='left', padx=(24, 8))
        self.track = tk.Canvas(self.frame, width=230, height=28,
                               background='#eeeeee', highlightthickness=2,
                               highlightbackground='#eeeeee',
                               highlightcolor='#2474c7', takefocus=True)
        self.track.pack(side='left', fill='x', expand=True)
        self.track.create_line(12, 14, 218, 14, width=4, fill='#888888', tags='rail')
        self.track.create_line(12, 14, 12, 14, width=4, fill='#2474c7', tags='fill')
        self.track.create_rectangle(9, 3, 15, 25, fill='#2474c7',
                                    outline='#174b82', tags='thumb')
        self.label = ttk.Label(self.frame, width=5, anchor='e')
        self.label.pack(side='left', padx=(8, 0))
        self.track.bind('<Configure>', lambda event: self.refresh())
        self.track.bind('<Button-1>', self.start)
        self.track.bind('<B1-Motion>', self.move)
        self.track.bind('<ButtonRelease-1>', self.finish)
        self.track.bind('<FocusOut>', app._cancel_thickness)
        for key, delta in (('Left', -1), ('Down', -1), ('Right', 1), ('Up', 1)):
            self.track.bind('<' + key + '>',
                            lambda event, delta=delta: app._change_size(delta))
        self.refresh()

    def refresh(self):
        self.swatch.configure(background=self.app.line_color)
        width = max(30, self.track.winfo_width())
        ratio = ((self.app.pencil_size - self.minimum) /
                 (self.maximum - self.minimum))
        x = 12 + ratio * (width - 24)
        self.track.coords('rail', 12, 14, width - 12, 14)
        self.track.coords('fill', 12, 14, x, 14)
        self.track.coords('thumb', x - 3, 3, x + 3, 25)
        self.label.configure(text=f'{size_percent(self.app.pencil_size, self.minimum, self.maximum)}%')

    def start(self, event):
        self.track.focus_set()
        self.app._begin_thickness()
        return self.move(event)

    def move(self, event):
        if self.app._thickness_gesture is not None:
            width = max(30, self.track.winfo_width())
            percent = 100 * (event.x - 12) / (width - 24)
            self.app._set_size(size_from_percent(percent, self.minimum, self.maximum),
                               record=False)
        return 'break'

    def finish(self, event):
        self.move(event)
        self.app._finish_thickness()
        self.app.canvas.focus_set()
        return 'break'
