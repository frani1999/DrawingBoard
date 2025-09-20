import tkinter as tk
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


def start_drawing(event):
    global is_drawing, last_x, last_y
    is_drawing = True
    last_x, last_y = event.x, event.y


def stop_drawing(event):
    global is_drawing
    is_drawing = False


def draw(event):
    global last_x, last_y
    if is_drawing:
        line = canvas.create_line(last_x, last_y, event.x, event.y, fill=line_color)
        print(line)
        lines.append(line)
        last_x, last_y = event.x, event.y


def undo(event):
    if lines:
        canvas.delete(lines.pop())


def switch_theme(event):
    global background_color, line_color
    background_color = BLACK if background_color == WHITE else WHITE
    line_color = WHITE if line_color == BLACK else BLACK
    for line in lines:
        canvas.itemconfig(line, fill=line_color)
    canvas.configure(background=background_color)


def save_draw(event):
    # File names
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ps_file = f"DrawingBoard_{timestamp}.ps"
    png_file = f"DrawingBoard_{timestamp}.png"

    # Create a background rectangle for save all image components
    rect_id = canvas.create_rectangle(0, 0,
                                      canvas.winfo_width(), canvas.winfo_height(),
                                      fill=background_color, outline="")
    canvas.tag_lower(rect_id)

    # Create ps file
    canvas.postscript(file=ps_file, colormode='color')
    # Transform ps file to png using PILLOW
    img = Image.open(ps_file)
    img.save(png_file)
    # Close and delete ps file, delete created rectangle
    img.close()
    os.remove(ps_file)
    canvas.delete(rect_id)
    showinfo("Drawing Board info", f"Image saved successfully as {png_file}")


def show_help(event):
    text = "keyboard shortcuts:\n" \
           "·Ctrl+z → Undo lines\n" \
           "·Ctrl+t → Switch between black and white theme\n" \
           "·Ctrl+s → Save current drawing as a png image\n" \
           "·Ctrl+h → Show keyboard shortcuts help"
    showinfo("Drawing Board Help", text)


# Create Menubar
menubar = tk.Menu(window)
window.config(menu=menubar)

file_menu = tk.Menu(menubar, tearoff=False)
file_menu.add_command(label='Save Drawing', accelerator='Ctrl+s', command=window.destroy)
file_menu.add_separator()
file_menu.add_command(label='Exit', command=window.destroy)

view_menu = tk.Menu(menubar, tearoff=False)
view_menu.add_command(label='Switch Theme', accelerator='Ctrl+t', command=window.destroy)

help_menu = tk.Menu(menubar, tearoff=False)
help_menu.add_command(label='show Help', accelerator='Ctrl+h', command=window.destroy)

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

window.mainloop()
