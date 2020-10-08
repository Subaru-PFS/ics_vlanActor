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


def line(image, start_position, end_position, thickness, color):

    if start_position[0] == end_position[0]:
        vline(image, start_position, end_position[1] - start_position[1] + (-1 if end_position[1] < start_position[1] else 1), thickness, color)
    elif start_position[1] == end_position[1]:
        hline(image, start_position, end_position[0] - start_position[0] + (-1 if end_position[0] < start_position[0] else 1), thickness, color)
    else:
        pass  # not supported


def hline(image, position, length, thickness, color):

    image[position[1]:position[1] + thickness, position[0]:position[0] + length:(-1 if length < 0 else 1)] = color


def vline(image, position, length, thickness, color):

    image[position[1]:position[1] + length:(-1 if length < 0 else 1), position[0]:position[0] + thickness] = color


def crop(image, position, size):

    return image[position[1]:position[1] + size[1], position[0]:position[0] + size[0]]
