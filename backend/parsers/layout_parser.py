from collections import defaultdict

import pdfplumber


def extract_layout_rows(
    file_path: str,
    y_tolerance: float = 5
) -> list:
    """
    Extract PDF words using coordinates and reconstruct
    rows based on their vertical position.

    Returns:
        [
            {
                "page": 1,
                "top": 100.2,
                "text": "Patient Name : MADHUMITA (62Y/F)"
            }
        ]
    """

    all_rows = []

    with pdfplumber.open(file_path) as pdf:

        for page_number, page in enumerate(
            pdf.pages,
            start=1
        ):

            words = page.extract_words(
                use_text_flow=False,
                keep_blank_chars=False
            )

            rows = group_words_into_rows(
                words,
                y_tolerance=y_tolerance
            )

            for row in rows:

                all_rows.append({
                    "page": page_number,
                    "top": row["top"],
                    "text": row["text"]
                })

    return all_rows


def group_words_into_rows(
    words: list,
    y_tolerance: float = 5
) -> list:
    """
    Group words into visual rows based on Y coordinate.
    Then sort each row by X coordinate.
    """

    if not words:
        return []

    # Sort top-to-bottom first
    sorted_words = sorted(
        words,
        key=lambda word: (
            word["top"],
            word["x0"]
        )
    )

    rows = []

    current_row = []
    current_y = None

    for word in sorted_words:

        word_y = word["top"]

        if current_y is None:

            current_y = word_y
            current_row.append(word)

        elif abs(word_y - current_y) <= y_tolerance:

            current_row.append(word)

        else:

            rows.append(
                build_row(current_row)
            )

            current_row = [word]
            current_y = word_y

    if current_row:

        rows.append(
            build_row(current_row)
        )

    return rows


def build_row(words: list) -> dict:
    """
    Sort words left-to-right and rebuild the row.
    """

    sorted_row = sorted(
        words,
        key=lambda word: word["x0"]
    )

    text = " ".join(
        word["text"]
        for word in sorted_row
    )

    return {
        "top": min(
            word["top"]
            for word in sorted_row
        ),
        "text": text.strip()
    }


def rows_to_text(rows: list) -> str:
    """
    Convert reconstructed rows to readable text.
    """

    return "\n".join(
        row["text"]
        for row in rows
    )