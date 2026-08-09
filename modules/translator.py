def load_translation(text):
    """
    Read Myanmar translation lines.
    Empty lines are ignored.
    """

    if not text:
        return []

    return [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]


def match_translation(boxes, translations):
    """
    Match translation lines with OCR boxes.
    """

    result = []

    for index, box in enumerate(boxes):

        item = dict(box)

        if index < len(translations):
            item["myanmar"] = translations[index]
        else:
            item["myanmar"] = ""

        result.append(item)

    return result
