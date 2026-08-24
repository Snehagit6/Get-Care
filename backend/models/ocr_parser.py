import cv2
import numpy as np
import pypdfium2 as pdfium
import pytesseract


def preprocess_image(
    image
):

    image_array = np.array(
        image
    )

    if len(image_array.shape) == 3:

        gray = cv2.cvtColor(
            image_array,
            cv2.COLOR_RGB2GRAY
        )

    else:

        gray = image_array

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

    return processed


def extract_pdf_with_ocr(
    file_path: str
) -> str:

    pdf = pdfium.PdfDocument(
        file_path
    )

    pages_text = []

    for page_number in range(
        len(pdf)
    ):

        page = pdf[page_number]

        bitmap = page.render(
            scale=2
        )

        image = bitmap.to_pil()

        processed = preprocess_image(
            image
        )

        text = (
            pytesseract
            .image_to_string(
                processed,
                lang="eng",
                config="--psm 6"
            )
        )

        pages_text.append(
            f"\n--- PAGE "
            f"{page_number + 1} ---\n"
            f"{text}"
        )

    return "\n".join(
        pages_text
    )