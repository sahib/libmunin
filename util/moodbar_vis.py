import cairo
from gi.repository import Pango, PangoCairo
from collections import deque


def draw_text_at_pos(ctx, x, y, text, font_size=15):
    layout = PangoCairo.create_layout(ctx)
    font = Pango.FontDescription.from_string('Ubuntu Light')
    font.set_size(font_size * Pango.SCALE)
    layout.set_font_description(font)
    layout.set_markup(text, -1)
    layout.set_alignment(Pango.Alignment.LEFT)

    fw, fh = [num / Pango.SCALE / 2 for num in layout.get_size()]
    ctx.move_to(x, y)
    PangoCairo.show_layout(ctx, layout)


def draw(ctx, rgb, w, h):
    n = len(rgb)
    s = w / n

    for idx, (r, g, b) in enumerate(rgb):
        ctx.set_source_rgb(r, g, b)
        ctx.rectangle(idx * s, 0, s + 1, h)
        ctx.fill()

    ctx.set_source_rgb(0, 0, 0)
    ctx.rectangle(0, h - h / 6, w, h / 6)
    ctx.fill()

    ctx.set_source_rgb(1, 1, 1)

    for i in range(0, w, 100):
        draw_text_at_pos(ctx, s * i, h - h / 5, str(i) + '')


def read_moodbar_values(path):
    rgb_values = deque()
    with open(path, 'rb') as handle:
        while True:
            rgb = handle.read(3)
            if not rgb:
                break
            rgb_values.append(tuple(c / 255 for c in rgb))

    return rgb_values

if __name__ == '__main__':
    rgb_values = read_moodbar_values('mood.file')
    w, h = 1000, 100
    surface = cairo.PDFSurface('/tmp/mood.out', w, h)
    ctx = cairo.Context(surface)
    draw(ctx, rgb_values, w, h)
    surface.finish()
    surface.flush()
