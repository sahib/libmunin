from cairo import PDFSurface, Context
from gi.repository import Pango, PangoCairo
from collections import deque


def draw_text_at_pos(ctx, x, y, text, font_size=6):
    layout = PangoCairo.create_layout(ctx)
    font = Pango.FontDescription.from_string('Ubuntu Light')
    font.set_size(font_size * Pango.SCALE)
    layout.set_font_description(font)
    layout.set_markup(text, -1)

    fw, fh = [num / Pango.SCALE / 2 for num in layout.get_size()]
    ctx.move_to(x, y)
    PangoCairo.show_layout(ctx, layout)


def draw_moodbar(ctx, rgb, w, h):
    step = w / len(rgb)

    for idx, (r, g, b) in enumerate(rgb):
        # Set the color for the current stripe
        ctx.set_source_rgb(r, g, b)

        # plus one to fill the gap between stripes
        # (cairo uses sub pixel accuracy)
        ctx.rectangle(idx * step, 0, step + 0.5, h)
        ctx.fill()

    # Pain the black border down there:
    ctx.set_source_rgb(0, 0, 0)
    ctx.rectangle(0, h - h / 6, w, h / 6)
    ctx.fill()

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
        while True:
            rgb = handle.read(3)
            if not rgb:
                break
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
