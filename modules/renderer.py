from PIL import Image, ImageDraw, ImageFont

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

    result = image.copy()

    draw = ImageDraw.Draw(result)

    width, height = result.size

    x = max(0, int(box["x"]))
    y = max(0, int(box["y"]))

    w = max(1, int(box["w"]))
    h = max(1, int(box["h"]))

    x2 = min(width, x + w)
    y2 = min(height, y + h)

    # Small padding
    pad_x = max(2, min(8, int(w * 0.05)))
    pad_y = max(2, min(8, int(h * 0.10)))

    x1 = max(0, x - pad_x)
    y1 = max(0, y - pad_y)
    x3 = min(width, x2 + pad_x)
    y3 = min(height, y2 + pad_y)

    # Sample a nearby pixel.
    sample_x = max(0, min(width - 1, x1))
    sample_y = max(0, min(height - 1, y1))

    background = result.getpixel(
        (sample_x, sample_y)
    )

    draw.rectangle(
        [x1, y1, x3, y3],
        fill=background
    )

    return result


def _wrap_text(
    draw,
    text,
    font,
    max_width
):

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

        text_width = (
            bbox[2] - bbox[0]
        )

        if text_width <= max_width:

            current = test

        else:

            if current:

                lines.append(
                    current
                )

            current = word

    if current:

        lines.append(
            current
        )

    return lines


def replace_text(
    image,
    matched,
    translations
):

    result = image.copy()

    # Clean detected regions.
    for box in matched:

        text = box.get(
            "myanmar",
            ""
        ).strip()

        if not text:

            continue

        result = _clean_region(
            result,
            box
        )


    draw = ImageDraw.Draw(
        result
    )


    for box in matched:

        text = box.get(
            "myanmar",
            ""
        ).strip()

        if not text:

            continue


        x = int(box["x"])
        y = int(box["y"])
        w = int(box["w"])
        h = int(box["h"])


        font_size = max(
            16,
            min(
                42,
                int(h * 1.05)
            )
        )


        font = _get_font(
            font_size
        )


        max_width = max(
            40,
            int(w * 2.2)
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
        ) + 3


        total_height = (
            line_height *
            len(lines)
        )


        start_y = y + max(
            0,
            (h - total_height) // 2
        )


        for line_index, line in enumerate(
            lines
        ):

            draw.text(

                (
                    x,
                    start_y +
                    line_index *
                    line_height
                ),

                line,

                font=font,

                fill=(0, 0, 0)
            )


    return result
