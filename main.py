import tkinter as tk
from tkinter import filedialog
from PIL import Image
from datetime import datetime
import os
from tkinter.messagebox import showinfo

BLACK = 'black'
WHITE = 'white'
CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600

is_drawing = False
last_x, last_y = 0, 0
lines = []
background_color = WHITE
line_color = BLACK

# Root window
window = tk.Tk()
window.title("Drawing Board")


def start_drawing(event=None):
    global is_drawing, last_x, last_y
    is_drawing = True
    last_x, last_y = event.x, event.y


def stop_drawing(event=None):
    global is_drawing
    is_drawing = False


def draw(event=None):
    global last_x, last_y
    if is_drawing:
        line = canvas.create_line(last_x, last_y, event.x, event.y, fill=line_color)
        print(line)
        lines.append(line)
        last_x, last_y = event.x, event.y


def undo(event=None):
    if lines:
        canvas.delete(lines.pop())


def switch_theme(event=None):
    global background_color, line_color
    background_color = BLACK if background_color == WHITE else WHITE
    line_color = WHITE if line_color == BLACK else BLACK
    for line in lines:
        canvas.itemconfig(line, fill=line_color)
    canvas.configure(background=background_color)


def save_draw(event=None):
    # File names
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ps_file = f"DrawingBoard_{timestamp}.ps"
    png_file = f"DrawingBoard_{timestamp}.png"

    # Open window for select the path
    file_path = filedialog.asksaveasfilename(defaultextension=".png", initialfile=png_file,
                                             filetypes=[("PNG files", "*.png"),
                                                        ("JPEG files", "*.jpg;*.jpeg"),
                                                        ("All files", "*.*")])
    if not file_path:  # User cancel
        return

    # Create a background rectangle for save all image components
    rect_id = canvas.create_rectangle(0, 0, canvas.winfo_width(), canvas.winfo_height(),
                                      fill=background_color, outline="")
    canvas.tag_lower(rect_id)

    # Create ps file in file_path
    ps_path = file_path.split('/')
    ps_path[-1] = ps_file
    ps_path = "/".join(ps_path)
    canvas.postscript(file=ps_path, colormode='color')
    # Transform ps file to png using PILLOW
    img = Image.open(ps_path)
    img.save(file_path)
    # Close and delete ps file, delete created rectangle
    img.close()
    os.remove(ps_path)
    canvas.delete(rect_id)
    showinfo("Drawing Board info", f"Image saved successfully as {file_path.split('/')[-1]}")


def show_help(event=None):
    text = "keyboard shortcuts:\n" \
           "·Ctrl+z → Undo lines\n" \
           "·Ctrl+t → Switch between black and white theme\n" \
           "·Ctrl+s → Save current drawing as a png image\n" \
           "·Ctrl+h → Show keyboard shortcuts help"
    showinfo("Drawing Board Help", text)


def import_image(event=None):
    print("TO BE DEVELOPED")


# Create Menubar
menubar = tk.Menu(window)
window.config(menu=menubar)

file_menu = tk.Menu(menubar, tearoff=False)
file_menu.add_command(label='Save Drawing', accelerator='Ctrl+S', command=save_draw)
file_menu.add_command(label='Import Image', accelerator='Ctrl+I', command=import_image)
file_menu.add_separator()
file_menu.add_command(label='Exit', command=window.destroy)

view_menu = tk.Menu(menubar, tearoff=False)
view_menu.add_command(label='Switch Theme', accelerator='Ctrl+T', command=switch_theme)

help_menu = tk.Menu(menubar, tearoff=False)
help_menu.add_command(label='Show Help', accelerator='Ctrl+H', command=show_help)

# add the menus to the menubar
menubar.add_cascade(menu=file_menu, label="File")
menubar.add_cascade(menu=view_menu, label="View")
menubar.add_cascade(menu=help_menu, label="Help")

canvas = tk.Canvas(window, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg=background_color)
canvas.pack()


canvas.bind('<Button-1>', start_drawing)
canvas.bind('<ButtonRelease-1>', stop_drawing)
canvas.bind('<B1-Motion>', draw)
window.bind('<Control-z>', undo)
window.bind('<Control-t>', switch_theme)
window.bind('<Control-s>', save_draw)
window.bind('<Control-h>', show_help)
window.bind('<Control-i>', import_image)

window.mainloop()
