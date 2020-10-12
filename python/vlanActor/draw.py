from font8x8_basic import font8x8_basic


def text(image, position, text, color):

    _FONTSIZE = 8

    x0, y0 = position
    for i in range(len(text)):
        font = font8x8_basic[ord(text[i])]
        for dy in range(_FONTSIZE):
            y = y0 - dy
            if y < image.shape[0]:
                for dx in range(_FONTSIZE):
                    x = x0 + _FONTSIZE * i + dx
                    if x < image.shape[1] and font[dy] & (1 << dx):
                        image[y, x] = color


def line(image, start_position, end_position, color):

    if start_position[0] == end_position[0]:
        vline(image, start_position, end_position[1] - start_position[1] + (-1 if end_position[1] < start_position[1] else 1), color)
    elif start_position[1] == end_position[1]:
        hline(image, start_position, end_position[0] - start_position[0] + (-1 if end_position[0] < start_position[0] else 1), color)
    else:
        _line(image, start_position, end_position, color)


def _line(image, start_position, end_position, color):

    # bresenham's line algorithm
    x0, y0 = start_position
    x1, y1 = end_position
    sx = -1 if x0 > x1 else 1
    dx = x0 - x1 if sx < 0 else x1 - x0
    sy = -1 if y0 > y1 else 1
    dy = y0 - y1 if sy > 0 else y1 - y0
    e = dx + dy
    while True:
        image[y0, x0] = color
        e2 = e + e
        if e2 >= dy:
            if x0 == x1:
                break
            e += dy
            x0 += sx
        if e2 <= dx:
            if y0 == y1:
                break
            e += dx
            y0 += sy


def hline(image, position, length, color):

    image[position[1], position[0]:position[0] + length:(-1 if length < 0 else 1)] = color


def vline(image, position, length, color):

    image[position[1]:position[1] + length:(-1 if length < 0 else 1), position[0]] = color


def crop(image, position, size):

    return image[position[1]:position[1] + size[1], position[0]:position[0] + size[0]]
