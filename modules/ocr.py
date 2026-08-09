import pytesseract
import cv2
import numpy as np


def detect_text(image):
    """
    Detect text regions from a PIL image.
    Returns bounding boxes sorted top-to-bottom, left-to-right.
    """

    img = np.array(image)

    if img.ndim == 2:
        gray = img
    else:
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    data = pytesseract.image_to_data(
        gray,
        output_type=pytesseract.Output.DICT,
        config="--psm 11"
    )

    boxes = []

    for i in range(len(data["text"])):

        text = data["text"][i].strip()

        try:
            confidence = float(data["conf"][i])
        except Exception:
            confidence = 0

        if not text or confidence < 25:
            continue

        x = int(data["left"][i])
        y = int(data["top"][i])
        w = int(data["width"][i])
        h = int(data["height"][i])

        if w <= 2 or h <= 2:
            continue

        boxes.append({
            "text": text,
            "x": x,
            "y": y,
            "w": w,
            "h": h,
            "confidence": confidence
        })

    boxes.sort(
        key=lambda b: (b["y"], b["x"])
    )

    return boxes
