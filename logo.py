"""Drawing Board's geometric board-and-pencil logo."""

from PIL import Image, ImageDraw


def create_logo(size=64):
    """Render at high resolution so small window icons remain smooth."""
    image = Image.new('RGBA', (256, 256))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((8, 8, 248, 248), radius=52, fill='#16324f')
    draw.rounded_rectangle((48, 44, 194, 211), radius=16, fill='#f7fafc')
    draw.line((72, 174, 96, 158, 114, 172, 146, 142),
              fill='#2a9d8f', width=10, joint='curve')
    draw.polygon(((104, 138), (177, 65), (203, 91), (130, 164)), fill='#f4b942')
    draw.polygon(((104, 138), (94, 174), (130, 164)), fill='#e9c9a4')
    draw.polygon(((98, 160), (94, 174), (108, 170)), fill='#16324f')
    draw.polygon(((177, 65), (187, 55), (213, 81), (203, 91)), fill='#e76f51')
    return image.resize((size, size), Image.Resampling.LANCZOS)
