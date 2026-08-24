from PIL import Image
import numpy as np
import cv2
import pytesseract


def extract_image_with_ocr(
    file_path: str
) -> str:

    image = Image.open(
        file_path
    )

    image_array = np.array(
        image.convert("RGB")
    )

    gray = cv2.cvtColor(
        image_array,
        cv2.COLOR_RGB2GRAY
    )

    enlarged = cv2.resize(
        gray,
        None,
        fx=2,
        fy=2,
        interpolation=cv2.INTER_CUBIC
    )

    processed = cv2.threshold(
        enlarged,
        0,
        255,
        cv2.THRESH_BINARY
        + cv2.THRESH_OTSU
    )[1]

    text = pytesseract.image_to_string(
        processed,
        lang="eng",
        config="--psm 6"
    )

    return text