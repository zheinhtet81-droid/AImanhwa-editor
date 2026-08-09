import csv
import re

from docx import Document


def load_translation(text):
    """
    Read Myanmar translation lines.

    Empty lines are ignored.
    """

    if not text:
        return []

    return [
        line.strip()
        for line in str(text).splitlines()
        if line.strip()
    ]


def load_translation_file(path):
    """
    Read translation text from:

    .txt
    .docx
    .srt
    .vtt
    .csv
    """

    if not path:
        return []

    lower = path.lower()

    # TXT
    if lower.endswith(".txt"):

        with open(
            path,
            "r",
            encoding="utf-8-sig"
        ) as file:

            return load_translation(
                file.read()
            )


    # DOCX
    if lower.endswith(".docx"):

        document = Document(path)

        lines = []

        for paragraph in document.paragraphs:

            text = paragraph.text.strip()

            if text:
                lines.append(text)

        return lines


    # SRT
    if lower.endswith(".srt"):

        with open(
            path,
            "r",
            encoding="utf-8-sig"
        ) as file:

            content = file.read()

        lines = []

        for line in content.splitlines():

            line = line.strip()

            if not line:
                continue

            # Skip subtitle number
            if line.isdigit():
                continue

            # Skip timestamp
            if "-->" in line:
                continue

            lines.append(line)

        return lines


    # VTT
    if lower.endswith(".vtt"):

        with open(
            path,
            "r",
            encoding="utf-8-sig"
        ) as file:

            content = file.read()

        lines = []

        for line in content.splitlines():

            line = line.strip()

            if not line:
                continue

            if line.upper() == "WEBVTT":
                continue

            if "-->" in line:
                continue

            # Skip cue settings / numeric IDs
            if line.isdigit():
                continue

            lines.append(line)

        return lines


    # CSV
    if lower.endswith(".csv"):

        lines = []

        with open(
            path,
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as file:

            reader = csv.reader(file)

            for row in reader:

                for cell in row:

                    cell = cell.strip()

                    if cell:
                        lines.append(cell)

        return lines


    raise ValueError(
        "Supported translation files: "
        ".txt, .docx, .srt, .vtt, .csv"
    )


def match_translation(boxes, translations):
    """
    Match translation lines with OCR boxes.
    """

    result = []

    for index, box in enumerate(boxes):

        item = dict(box)

        if index < len(translations):

            item["myanmar"] = (
                translations[index]
            )

        else:

            item["myanmar"] = ""

        result.append(item)

    return result
