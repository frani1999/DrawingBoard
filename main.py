import tkinter as tk
from tkinter import colorchooser, filedialog, ttk
from tkinter import font as tkfont
from tkinter.messagebox import askokcancel, showinfo
from PIL import Image, ImageTk
from datetime import datetime
import os
from logo import create_logo
from eraser import remaining_segments

BLACK = 'black'
WHITE = 'white'
CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600
MIN_PENCIL_SIZE = 1
MAX_PENCIL_SIZE = 50


class DrawingBoardApp:
    def __init__(self, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg_color=WHITE, line_color=None):
        self.width = width
        self.height = height
        self.background_color = bg_color
        self._custom_color = line_color is not None
        self.line_color = line_color if self._custom_color else (
            WHITE if bg_color == BLACK else BLACK)
        self.pencil_size = MIN_PENCIL_SIZE
        self._cursor_position = None
        self.active_tool = 'pencil'
        self._erase_action = None

        self.is_drawing = False
        self._stroke_moved = False
        self.last_x = 0
        self.last_y = 0

        self.items = []

        # References to imported images to avoid GC
        self._image_refs = []

        self.window = tk.Tk()
        self.window.title("Drawing Board")
        self._logo = ImageTk.PhotoImage(create_logo(), master=self.window)
        self.window.iconphoto(True, self._logo)
        self._help_window = None
        self._build_menu()
        self.canvas = tk.Canvas(self.window, width=self.width, height=self.height,
                                bg=self.background_color, cursor='pencil')
        self.canvas.pack()
        self._cursor_outline = self.canvas.create_oval(
            0, 0, 0, 0, outline=self.line_color, state='hidden')
        self._rubber_icon = self.canvas.create_polygon(
            0, 0, 0, 0, 0, 0, fill='#f19ab5', outline='#263445',
            width=1, state='hidden')
        self._rubber_sleeve = self.canvas.create_polygon(
            0, 0, 0, 0, 0, 0, fill='#dce7f0', outline='#263445',
            width=1, state='hidden')

        # Bindings
        self._bind_events()

    def _build_menu(self):
        menubar = tk.Menu(self.window)
        self.window.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label='Save Drawing', accelerator='Ctrl+S', command=self.save_draw)
        file_menu.add_command(label='Import Image', accelerator='Ctrl+I', command=self.import_image)
        file_menu.add_command(label='Undo All', accelerator='Ctrl+Shift+Z', command=self.undo_all)
        file_menu.add_separator()
        file_menu.add_command(label='Exit', command=self.window.destroy)

        select_menu = tk.Menu(menubar, tearoff=False)
        select_menu.add_command(label='Color', accelerator='Ctrl+Shift+C', command=self.select_color)
        select_menu.add_command(label='Pencil', accelerator='Ctrl+Shift+P', command=self.select_pencil)
        select_menu.add_command(label='Rubber', accelerator='Ctrl+Shift+R', command=self.select_rubber)

        view_menu = tk.Menu(menubar, tearoff=False)
        view_menu.add_command(label='Switch Theme', accelerator='Ctrl+T', command=self.switch_theme)

        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label='Show Help', accelerator='Ctrl+H', command=self.show_help)

        menubar.add_cascade(menu=file_menu, label="File")
        menubar.add_cascade(menu=select_menu, label="Select")
        menubar.add_cascade(menu=view_menu, label="View")
        menubar.add_cascade(menu=help_menu, label="Help")

    def _bind_events(self):
        # Mouse events for drawing
        self.canvas.bind('<Button-1>', self.start_drawing)
        self.canvas.bind('<ButtonRelease-1>', self.stop_drawing)
        self.canvas.bind('<B1-Motion>', self.draw)
        self.canvas.bind('<Enter>', self._move_cursor)
        self.canvas.bind('<Motion>', self._move_cursor)
        self.canvas.bind('<Leave>', self._hide_cursor)

        # Keyboard shortcuts (bindings on window)
        self.window.bind('<Control-z>', self.undo)
        self.window.bind('<Control-Shift-Z>', self.undo_all)
        self.window.bind('<Control-t>', self.switch_theme)
        self.window.bind('<Control-s>', self.save_draw)
        self.window.bind('<Control-h>', self.show_help)
        self.window.bind('<Control-i>', self.import_image)
        self.window.bind('<Control-Shift-C>', self.select_color)
        self.window.bind('<Control-Shift-R>', self.select_rubber)
        self.window.bind('<Control-Shift-P>', self.select_pencil)
        for key in ('plus', 'equal', 'KP_Add'):
            self.window.bind(f'<Control-{key}>', self.increase_pencil_size)
        for key in ('minus', 'KP_Subtract'):
            self.window.bind(f'<Control-{key}>', self.decrease_pencil_size)

    def _move_cursor(self, event):
        self._cursor_position = (event.x, event.y)
        self._update_cursor()

    def _hide_cursor(self, event=None):
        self._cursor_position = None
        self.canvas.itemconfigure(self._cursor_outline, state='hidden')
        self.canvas.itemconfigure(self._rubber_icon, state='hidden')
        self.canvas.itemconfigure(self._rubber_sleeve, state='hidden')

    def _update_cursor(self):
        if self._cursor_position is None:
            return
        x, y = self._cursor_position
        radius = self.pencil_size / 2
        self.canvas.coords(self._cursor_outline,
                           x - radius, y - radius, x + radius, y + radius)
        color = self.line_color if self.active_tool == 'pencil' else (
            WHITE if self.background_color == BLACK else BLACK)
        self.canvas.itemconfigure(self._cursor_outline, outline=color, state='normal')
        self.canvas.tag_raise(self._cursor_outline)
        if self.active_tool == 'rubber':
            self.canvas.coords(self._rubber_icon,
                               x + 5, y - 5, x + 17, y - 17,
                               x + 28, y - 6, x + 16, y + 6)
            self.canvas.coords(self._rubber_sleeve,
                               x + 11, y - 11, x + 17, y - 17,
                               x + 28, y - 6, x + 22, y)
            for item in (self._rubber_icon, self._rubber_sleeve):
                self.canvas.itemconfigure(item, state='normal')
                self.canvas.tag_raise(item)

    def _select_tool(self, tool):
        self.stop_drawing()
        self.active_tool = tool
        self.canvas.configure(cursor='pencil' if tool == 'pencil' else 'none')
        if tool == 'pencil':
            self.canvas.itemconfigure(self._rubber_icon, state='hidden')
            self.canvas.itemconfigure(self._rubber_sleeve, state='hidden')
        self._update_cursor()
        return 'break'

    def select_pencil(self, event=None):
        return self._select_tool('pencil')

    def select_rubber(self, event=None):
        return self._select_tool('rubber')

    def increase_pencil_size(self, event=None):
        self.pencil_size = min(MAX_PENCIL_SIZE, self.pencil_size + 1)
        self._update_cursor()
        return 'break'

    def decrease_pencil_size(self, event=None):
        self.pencil_size = max(MIN_PENCIL_SIZE, self.pencil_size - 1)
        self._update_cursor()
        return 'break'

    def start_drawing(self, event=None):
        if event:
            self.is_drawing = True
            self._stroke_moved = False
            self.last_x, self.last_y = event.x, event.y
            if self.active_tool == 'rubber':
                self._erase_action = None
                self._erase_to(event.x, event.y)
                self._move_cursor(event)

    def stop_drawing(self, event=None):
        if (event is not None and self.is_drawing
                and self.active_tool == 'pencil' and not self._stroke_moved):
            radius = self.pencil_size / 2
            dot = self.canvas.create_oval(
                self.last_x - radius, self.last_y - radius,
                self.last_x + radius, self.last_y + radius,
                fill=self.line_color, outline='', tags=('pencil_dot',))
            self.items.append(dot)
            if not self._custom_color:
                self.canvas.addtag_withtag('theme_color', dot)
            self._update_cursor()
        self.is_drawing = False
        self._erase_action = None

    def draw(self, event=None):
        if not self.is_drawing or event is None:
            return
        if (event.x, event.y) == (self.last_x, self.last_y):
            return
        self._stroke_moved = True
        if self.active_tool == 'rubber':
            self._erase_to(event.x, event.y)
            self.last_x, self.last_y = event.x, event.y
            self._move_cursor(event)
            return
        line_id = self.canvas.create_line(
            self.last_x, self.last_y, event.x, event.y,
            fill=self.line_color, width=self.pencil_size, capstyle=tk.ROUND)
        self.items.append(line_id)
        if not self._custom_color:
            self.canvas.addtag_withtag('theme_color', line_id)
        self.last_x, self.last_y = event.x, event.y
        self._move_cursor(event)

    def undo(self, event=None):
        self.stop_drawing()
        if self.items:
            last_id = self.items.pop()
            if isinstance(last_id, dict):
                for original, replacements in reversed(last_id['erased']):
                    for item in replacements:
                        self.canvas.delete(item)
                    self.canvas.itemconfigure(original, state='normal')
                self._update_cursor()
            else:
                self.canvas.delete(last_id)

    def undo_all(self, event=None):
        self.stop_drawing()
        if askokcancel('Undo All', 'Are You sure you want to undo all design?',
                       parent=self.window, icon='warning', default='cancel'):
            # Keep imports in their original undo order and retain PhotoImages.
            images = []
            while self.items:
                item = self.items[-1]
                if not isinstance(item, dict) and self.canvas.type(item) == 'image':
                    images.append(self.items.pop())
                else:
                    self.undo()
            self.items.extend(reversed(images))
        self.canvas.focus_set()
        return 'break'

    def _erase_to(self, x, y):
        radius = self.pencil_size / 2
        start, end = (self.last_x, self.last_y), (x, y)
        candidates = self.canvas.find_overlapping(
            min(start[0], x) - radius, min(start[1], y) - radius,
            max(start[0], x) + radius, max(start[1], y) + radius)
        for item in candidates:
            item_type = self.canvas.type(item)
            is_dot = item_type == 'oval' and 'pencil_dot' in self.canvas.gettags(item)
            if item_type != 'line' and not is_dot:
                continue
            coords = tuple(self.canvas.coords(item))
            if is_dot:
                cx, cy = (coords[0] + coords[2]) / 2, (coords[1] + coords[3]) / 2
                if remaining_segments((cx, cy, cx, cy), start, end,
                                      radius + (coords[2] - coords[0]) / 2):
                    continue
                pieces = []
            else:
                width = float(self.canvas.itemcget(item, 'width'))
                pieces = remaining_segments(coords, start, end, radius + width / 2)
                if pieces == [coords]:
                    continue
            if self._erase_action is None:
                self._erase_action = {'erased': []}
                self.items.append(self._erase_action)
            replacements = []
            for piece in pieces:
                replacement = self.canvas.create_line(
                    *piece, fill=self.canvas.itemcget(item, 'fill'), width=width,
                    capstyle=tk.ROUND, tags=self.canvas.gettags(item))
                self.canvas.tag_lower(replacement, item)
                replacements.append(replacement)
            # Retain hidden originals so undo restores exact geometry and stacking.
            self.canvas.itemconfigure(item, state='hidden')
            self._erase_action['erased'].append((item, replacements))

    def select_color(self, event=None):
        self.stop_drawing()
        _, selected_color = colorchooser.askcolor(
            color=self.line_color, parent=self.window, title='Pencil Color')
        if selected_color:
            self.line_color = selected_color
            self._custom_color = True
            self._update_cursor()
        return 'break'

    def switch_theme(self, event=None):
        self.background_color = BLACK if self.background_color == WHITE else WHITE
        default_color = WHITE if self.background_color == BLACK else BLACK
        if not self._custom_color:
            self.line_color = default_color
        for item in self.canvas.find_withtag('theme_color'):
            self.canvas.itemconfig(item, fill=default_color)
        self.canvas.configure(background=self.background_color)
        self._update_cursor()

    def save_draw(self, event=None):
        # Force refresh to obtain correct sizes
        self.canvas.update()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        png_default = f"DrawingBoard_{timestamp}.png"
        file_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                 initialfile=png_default,
                                                 filetypes=[("PNG files", "*.png"),
                                                            ("JPEG files", "*.jpg;*.jpeg"),
                                                            ("All files", "*.*")])
        if not file_path:  # User cancel
            return

        # Create a temporal background rectangle for save all image components
        rect_id = self.canvas.create_rectangle(0, 0, self.canvas.winfo_width(),
                                               self.canvas.winfo_height(),
                                               fill=self.background_color, outline="")
        self.canvas.tag_lower(rect_id)
        self.canvas.update()

        # Create ps file in file_path
        dirpath = os.path.dirname(file_path) or '.'
        ps_filename = f"DrawingBoard_{timestamp}.ps"
        ps_path = os.path.join(dirpath, ps_filename)

        try:
            self.canvas.itemconfigure(self._cursor_outline, state='hidden')
            self.canvas.itemconfigure(self._rubber_icon, state='hidden')
            self.canvas.itemconfigure(self._rubber_sleeve, state='hidden')
            self.canvas.postscript(file=ps_path, colormode='color')

            # Convert PS -> PNG, JPG
            img = Image.open(ps_path)
            try:
                img.save(file_path)
            finally:
                img.close()
        except Exception as e:
            showinfo("Drawing Board error", f"Cannot save image {os.path.basename(file_path)}: {e}")
            return
        finally:
            self._update_cursor()
            # Delete ps file
            try:
                if os.path.exists(ps_path):
                    os.remove(ps_path)
            except Exception:
                pass
            # Delete temporal background rectangle
            try:
                self.canvas.delete(rect_id)
            except Exception:
                pass

        showinfo("Drawing Board info", f"Image saved successfully as {os.path.basename(file_path)}")

    def show_help(self, event=None):
        if self._help_window is not None and self._help_window.winfo_exists():
            self._help_window.lift()
            self._help_window.focus_set()
            return 'break'

        dialog = tk.Toplevel(self.window)
        self._help_window = dialog
        dialog.title('Drawing Board Help')
        dialog.transient(self.window)
        dialog.iconphoto(False, self._logo)
        dialog.resizable(False, False)
        body = ttk.Frame(dialog, padding=24)
        body.pack(fill='both', expand=True)
        # Keep the font alive and respect the platform's default font family/size.
        dialog.bold_font = tkfont.nametofont('TkDefaultFont').copy()
        dialog.bold_font.configure(weight='bold')
        ttk.Label(body, image=self._logo).grid(row=0, column=0, sticky='w', pady=(0, 16))
        ttk.Label(body, text='Drawing Board', font=dialog.bold_font).grid(
            row=0, column=1, sticky='w', padx=(12, 0), pady=(0, 16))
        ttk.Label(body, text='Keyboard shortcuts:', font=dialog.bold_font).grid(
            row=1, column=0, columnspan=2, sticky='w', padx=(16, 0), pady=(0, 8))
        shortcuts = (
            ('Ctrl+Z', 'Undo drawing, import, or rubber stroke'),
            ('Ctrl+Shift+Z', 'Undo All: clear pencil marks after confirmation'),
            ('Ctrl+T', 'Switch between black and white theme'),
            ('Ctrl+S', 'Save the current drawing as PNG or JPEG'),
            ('Ctrl+H', 'Show keyboard shortcuts help'),
            ('Ctrl+I', 'Import an image onto the canvas'),
            ('Ctrl+Shift+C', 'Open the color selector'),
            ('Ctrl+Shift+R', 'Select the rubber'),
            ('Ctrl+Shift+P', 'Select the pencil'),
            ('Ctrl++', 'Increase pencil / rubber size by 1 pixel'),
            ('Ctrl+-', 'Decrease pencil / rubber size by 1 pixel'),
        )
        for row, (command, description) in enumerate(shortcuts, start=2):
            ttk.Label(body, text=command, font=dialog.bold_font).grid(
                row=row, column=0, sticky='w', padx=(40, 12), pady=3)
            ttk.Label(body, text=f'→ {description}').grid(
                row=row, column=1, sticky='w', pady=3)
        size_row = len(shortcuts) + 2
        ttk.Label(body, text='Pencil / rubber size:', font=dialog.bold_font).grid(
            row=size_row, column=0, columnspan=2, sticky='w', padx=(16, 0), pady=(16, 8))
        details = (
            f'Minimum: {MIN_PENCIL_SIZE} pixel\n'
            f'Maximum: {MAX_PENCIL_SIZE} pixels\n'
            'Default: 1 pixel\n\n'
            'Adjustments stop at either limit.\n'
            'Both tools share the size; switching tools keeps it unchanged.\n'
            'The cursor outline shows the current tool size.\n'
            'Rubber erases pencil marks and preserves imported images.\n'
            'File → Undo All clears pencil marks and keeps imported images.\n'
            'Confirm with OK or choose Cancel to keep the design.\n'
            'Undo All cannot be reversed with Ctrl+Z.\n'
            'Ctrl+= and Ctrl + numeric keypad + / - also work.'
        )
        ttk.Label(body, text=details, justify='left').grid(
            row=size_row + 1, column=0, columnspan=2, sticky='w', padx=(40, 0))
        close = ttk.Button(body, text='Close', command=self._close_help)
        close.grid(row=size_row + 2, column=0, columnspan=2, sticky='e', pady=(16, 0))
        dialog.protocol('WM_DELETE_WINDOW', self._close_help)
        dialog.bind('<Escape>', self._close_help)
        dialog.bind('<Return>', self._close_help)
        close.focus_set()
        return 'break'

    def _close_help(self, event=None):
        if self._help_window is not None:
            self._help_window.destroy()
            self._help_window = None
            self.canvas.focus_set()
        return 'break'

    def import_image(self, event=None):
        filetypes = [("Image files", ("*.png", "*.jpg", "*.jpeg", "*.gif", "*.bmp")), ("All files", "*.*")]
        path = filedialog.askopenfilename(title="Import Image", filetypes=filetypes)
        if not path:
            return

        try:
            pil_img = Image.open(path)
        except Exception as e:
            showinfo("Import error", f"Cannot open Image {os.path.basename(path)}: {e}")
            return

        # Resize to fit on the canvas
        max_w, max_h = self.canvas.winfo_width(), self.canvas.winfo_height()
        img_w, img_h = pil_img.size
        scale = min(1.0, max_w / img_w, max_h / img_h)
        if scale < 1.0:
            new_size = (int(img_w * scale), int(img_h * scale))
            pil_img = pil_img.resize(new_size, Image.LANCZOS)

        tk_img = ImageTk.PhotoImage(pil_img)
        # Place image in centre
        x = self.canvas.winfo_width() // 2
        y = self.canvas.winfo_height() // 2
        img_id = self.canvas.create_image(x, y, image=tk_img)
        self.items.append(img_id)
        # Save reference so that Python does not delete it
        self._image_refs.append(tk_img)
        self._update_cursor()

    def run(self):
        self.window.mainloop()


if __name__ == "__main__":
    app = DrawingBoardApp()
    app.run()
