import tkinter as tk

BLACK = 'black'
WHITE = 'white'

window = tk.Tk()
window.title("Linkfy Drawing Board")

is_drawing = False
last_x, last_y = 0, 0
lines = []
background_color = WHITE
line_color = BLACK

canvas = tk.Canvas(window, width=800, height=600, bg=background_color)
canvas.pack()


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


canvas.bind('<Button-1>', start_drawing)
canvas.bind('<ButtonRelease-1>', stop_drawing)
canvas.bind('<B1-Motion>', draw)
window.bind('<Control-z>', undo)
window.bind('<Control-t>', switch_theme)

window.mainloop()
