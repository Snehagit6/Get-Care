from pypdf import PdfReader


def extract_pdf(file_path: str) -> str:
    """
    Extract normal text from a PDF.
    This is useful as raw/audit text and as a fallback.
    """

    reader = PdfReader(file_path)

    pages_text = []

    for page_number, page in enumerate(reader.pages, start=1):

        text = page.extract_text()

        if text and text.strip():

            pages_text.append(
                f"\n--- PAGE {page_number} ---\n"
                f"{text}"
            )

    return "\n".join(pages_text)