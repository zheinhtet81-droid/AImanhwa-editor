from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np


FONT_PATH = "fonts/Pyidaungsu.ttf"


def _get_font(size):
    try:
        return ImageFont.truetype(
            FONT_PATH,
            max(12, int(size))
        )
    except Exception:
        return ImageFont.load_default()


def _clean_region(image, box):

    img = np.array(image).copy()

    height, width = img.shape[:2]

    x = max(0, int(box["x"]))
    y = max(0, int(box["y"]))
    w = max(1, int(box["w"]))
    h = max(1, int(box["h"]))

    x2 = min(width, x + w)
    y2 = min(height, y + h)

    mask = np.zeros(
        (height, width),
        dtype=np.uint8
    )

    # Slightly expand the mask around the original text.
    pad_x = max(2, int(w * 0.08))
    pad_y = max(2, int(h * 0.15))

    mx1 = max(0, x - pad_x)
    my1 = max(0, y - pad_y)
    mx2 = min(width, x2 + pad_x)
    my2 = min(height, y2 + pad_y)

    mask[my1:my2, mx1:mx2] = 255

    try:
        cleaned = cv2.inpaint(
            img,
            mask,
            3,
            cv2.INPAINT_TELEA
        )

        return Image.fromarray(cleaned)

    except Exception:
        return image


def _wrap_text(draw, text, font, max_width):

    words = text.split()

    if not words:
        return []

    lines = []
    current = ""

    for word in words:

        test = (
            word
            if not current
            else current + " " + word
        )

        bbox = draw.textbbox(
            (0, 0),
            test,
            font=font
        )

        width = bbox[2] - bbox[0]

        if width <= max_width:
            current = test

        else:

            if current:
                lines.append(current)

            current = word

    if current:
        lines.append(current)

    return lines


def replace_text(image, matched, translations):

    result = image.copy()

    # Clean all detected regions first.
    for box in matched:

        if not box.get("myanmar"):
            continue

        result = _clean_region(
            result,
            box
        )

    draw = ImageDraw.Draw(result)

    for box in matched:

        text = box.get("myanmar", "").strip()

        if not text:
            continue

        x = int(box["x"])
        y = int(box["y"])
        w = int(box["w"])
        h = int(box["h"])

        # Adaptive font size.
        font_size = max(
            16,
            min(
                48,
                int(h * 1.15)
            )
        )

        font = _get_font(font_size)

        max_width = max(
            40,
            int(w * 2.5)
        )

        lines = _wrap_text(
            draw,
            text,
            font,
            max_width
        )

        if not lines:
            continue

        bbox = draw.textbbox(
            (0, 0),
            "မြ",
            font=font
        )

        line_height = max(
            18,
            bbox[3] - bbox[1]
        ) + 4

        total_height = (
            line_height * len(lines)
        )

        start_y = y + max(
            0,
            (h - total_height) // 2
        )

        for line_index, line in enumerate(lines):

            draw.text(
                (
                    x,
                    start_y
                    + line_index * line_height
                ),
                line,
                font=font,
                fill=(0, 0, 0),
                stroke_width=0
            )

    return result
