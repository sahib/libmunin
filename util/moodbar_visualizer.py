from cairo import PDFSurface, Context
from gi.repository import Pango, PangoCairo
from collections import deque
from itertools import zip_longest
from numpy import histogram


def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)



def draw_moodbar(ctx, rgb, w, h):
    step = w / len(rgb)
    ctx.set_source_rgb(0.25, 0.25, 0.25)
    ctx.paint()

    def draw_checker(height, width):
        own_step = width / len(rgb)

        odd = 0
        for idx in range(0, w, 50):
            if odd % 2 is 0:
                ctx.set_source_rgb(0.25, 0.25, 0.25)
            else:
                ctx.set_source_rgb(0.3, 0.3, 0.3)
            odd += 1

            ctx.rectangle(own_step * idx, 0, 101, h)
            ctx.fill()

    def draw_text_at_pos(ctx, x, y, text, font_size=6):
        layout = PangoCairo.create_layout(ctx)
        font = Pango.FontDescription.from_string('Ubuntu Light')
        font.set_size(font_size * Pango.SCALE)
        layout.set_font_description(font)
        layout.set_markup(text, -1)

        fw, fh = [num / Pango.SCALE / 2 for num in layout.get_size()]
        ctx.move_to(x, y)
        PangoCairo.show_layout(ctx, layout)

    def draw_graph(row, color, height, width):
        ctx.set_line_width(0.2)
        own_step = width / len(rgb)
        block_size = 5

        for idx in range(0, len(rgb) + block_size, block_size):
            block = rgb[idx:idx + block_size]
            value = sum(point[row] for point in block) / block_size
            ctx.line_to(idx * own_step, height - value * height)

        ctx.set_source_rgb(*color)
        ctx.stroke()

    def draw_histogram(row, x, height, width, color):
        ctx.set_source_rgb(0.1, 0.1, 0.1)
        ctx.rectangle(x, 0, width + 1, height)
        ctx.fill()

        block_size = 15
        own_step = width / 255
        hist, _ = histogram([int(point[row] * 255) for point in rgb], bins=(255 / block_size))

        # max_value = 255
        max_value = max(hist)

        idx = 0
        ctx.set_source_rgb(*color)
        for value in hist:
            value /= max_value
            ctx.rectangle(x + idx * own_step, height, own_step * (block_size - 1), -value * height)
            ctx.fill()
            idx += block_size

    draw_checker(40, 750)
    draw_graph(0, (1, 0, 0), height=40, width=750)
    draw_graph(1, (0, 1, 0), height=40, width=750)
    draw_graph(2, (0, 0, 1), height=40, width=750)

    ctx.set_source_rgb(1, 1, 1)
    ctx.rectangle(0, 40, w, 1)
    ctx.fill()

    for idx, (r, g, b) in enumerate(rgb):
        # Set the color for the current stripe
        ctx.set_source_rgb(r, g, b)

        # plus one to fill the gap between stripes
        # (cairo uses sub pixel accuracy)
        ctx.rectangle(idx * step, 41, step + 0.5, h)
        ctx.fill()

    # Pain the black border down there:
    ctx.set_source_rgb(0, 0, 0)
    ctx.rectangle(0, h - h / 6, w, h / 6 + 1)
    ctx.fill()

    draw_histogram(0, 760, 40, 80, (1.00, 0.75, 0.50))
    draw_histogram(1, 840, 40, 80, (0.50, 1.00, 0.50))
    draw_histogram(2, 920, 40, 80, (0.50, 0.75, 1.00))

    # Change color to white for the text:
    ctx.set_source_rgb(1, 1, 1)

    # Draw the scala:
    for i in range(0, w + 10, 10):
        x = min(max(step * i - 5, 0), w - 21)
        text = str(int(i / 10)) + '%'

        if i % 100 is 0:
            height, width = h / 15, 2
            draw_text_at_pos(ctx, x, h - height - 10, '<b>{}</b>'.format(text), font_size=6)
        elif i % 50 is 0:
            height, width = h / 20, 1.5
            draw_text_at_pos(ctx, x, h - height - 8, '<i>{}</i>'.format(text), font_size=5)
        else:
            height, width = h / 35, 0.75

        ctx.rectangle(min(step * i, w - step), h - height, width, height)
        ctx.fill()

    # Pain the little white border between moodbar and scala:
    ctx.rectangle(0, h - h / 6, w, 1)
    ctx.fill()


def read_moodbar_values(path):
    rgb_values = deque()
    with open(path, 'rb') as handle:
        vector = handle.read()

    for rgb in grouper(vector, n=3):
        rgb_values.append(tuple(c / 0xff for c in rgb))

    return list(rgb_values)


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('usage: {} [some_mood_file] [-i some_audio_file]'.format(sys.argv[0]))
        sys.exit(-1)

    if '-i' in sys.argv:
        from subprocess import call
        moodbar_file = '/tmp/mood.file'
        call(['moodbar', sys.argv[2], '-o', moodbar_file])
        print('Writing out to', moodbar_file)
    else:
        moodbar_file = sys.argv[1]

    # Read the rgb vector:
    rgb_values = read_moodbar_values(moodbar_file)

    w, h = 1000, 100
    surface = PDFSurface('/tmp/mood.out', w, h)
    draw_moodbar(Context(surface), rgb_values, w, h)
    surface.finish()
