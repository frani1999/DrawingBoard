import tkinter as tk
from tkinter import filedialog
from tkinter.messagebox import showinfo
from PIL import Image, ImageTk
from datetime import datetime
import os

BLACK = 'black'
WHITE = 'white'
CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600


class DrawingBoardApp:
    def __init__(self, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg_color=WHITE, line_color=BLACK):
        self.width = width
        self.height = height
        self.background_color = bg_color
        self.line_color = line_color

        self.is_drawing = False
        self.last_x = 0
        self.last_y = 0

        self.items = []

        # References to imported images to avoid GC
        self._image_refs = []

        self.window = tk.Tk()
        self.window.title("Drawing Board")
        self._build_menu()
        self.canvas = tk.Canvas(self.window, width=self.width, height=self.height, bg=self.background_color)
        self.canvas.pack()

        # Bindings
        self._bind_events()

    def _build_menu(self):
        menubar = tk.Menu(self.window)
        self.window.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label='Save Drawing', accelerator='Ctrl+S', command=self.save_draw)
        file_menu.add_command(label='Import Image', accelerator='Ctrl+I', command=self.import_image)
        file_menu.add_separator()
        file_menu.add_command(label='Exit', command=self.window.destroy)

        view_menu = tk.Menu(menubar, tearoff=False)
        view_menu.add_command(label='Switch Theme', accelerator='Ctrl+T', command=self.switch_theme)

        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label='Show Help', accelerator='Ctrl+H', command=self.show_help)

        menubar.add_cascade(menu=file_menu, label="File")
        menubar.add_cascade(menu=view_menu, label="View")
        menubar.add_cascade(menu=help_menu, label="Help")

    def _bind_events(self):
        # Mouse events for drawing
        self.canvas.bind('<Button-1>', self.start_drawing)
        self.canvas.bind('<ButtonRelease-1>', self.stop_drawing)
        self.canvas.bind('<B1-Motion>', self.draw)

        # Keyboard shortcuts (bindings on window)
        self.window.bind('<Control-z>', self.undo)
        self.window.bind('<Control-t>', self.switch_theme)
        self.window.bind('<Control-s>', self.save_draw)
        self.window.bind('<Control-h>', self.show_help)
        self.window.bind('<Control-i>', self.import_image)

    def start_drawing(self, event=None):
        if event:
            self.is_drawing = True
            self.last_x, self.last_y = event.x, event.y

    def stop_drawing(self, event=None):
        self.is_drawing = False

    def draw(self, event=None):
        if not self.is_drawing or event is None:
            return
        line_id = self.canvas.create_line(self.last_x, self.last_y, event.x, event.y, fill=self.line_color)
        self.items.append(line_id)
        self.last_x, self.last_y = event.x, event.y

    def undo(self, event=None):
        if self.items:
            last_id = self.items.pop()
            self.canvas.delete(last_id)

    def switch_theme(self, event=None):
        self.background_color = BLACK if self.background_color == WHITE else WHITE
        self.line_color = WHITE if self.line_color == BLACK else BLACK
        for item in self.canvas.find_all():
            if self.canvas.type(item) == 'line':
                self.canvas.itemconfig(item, fill=self.line_color)
        self.canvas.configure(background=self.background_color)

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
        text = ("keyboard shortcuts:\n"
                "·Ctrl+z → Undo lines\n"
                "·Ctrl+t → Switch between black and white theme\n"
                "·Ctrl+s → Save current drawing as a png image\n"
                "·Ctrl+h → Show keyboard shortcuts help\n"
                "·Ctrl+i → Import an image onto the canvas")
        showinfo("Drawing Board Help", text)

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

    def run(self):
        self.window.mainloop()


if __name__ == "__main__":
    app = DrawingBoardApp()
    app.run()
