import os
import sys
import json

from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from paths.path import REPORT_PATH, PARSED_REPORT_PATH

from backend.parsers.pdf_parser import extract_pdf
from backend.parsers.layout_parser import extract_layout_rows
from backend.parsers.ocr_parser import extract_pdf_with_ocr
from backend.parsers.image_parser import extract_image_with_ocr
from backend.parsers.docx_parser import extract_docx
from backend.extractors.metadata_extractor import extract_metadata_from_rows
from backend.extractors.medical_data_extractor import extract_medical_data
from backend.models.canonical_patient import create_canonical_report


def detect_file_type(file_path: str) -> str:
    """
    Detect file type based on extension.
    """

    return Path(file_path).suffix.lower().lstrip(".")


def parse_report(file_path: str) -> dict:
    """
    Main entry point for medical report processing.

    Input:
        PDF / scanned PDF / image / DOCX

    Output:
        Raw structured medical data
    """

    file_type = detect_file_type(file_path)


    if file_type == "pdf":

        # First attempt normal text extraction
        text = extract_pdf(file_path)
        print(f"Extracted text length: {len(text)} characters")
        # If insufficient text was extracted,
        # assume that the PDF may be scanned
        if not text or len(text.strip()) < 100:
            extraction_method = "ocr_pdf"
            text = extract_pdf_with_ocr(file_path)
        else:
            extraction_method = "pdf_text"

        rows = extract_layout_rows(file_path)

        if not rows:
            rows = [
                {"page": 1, "text": line}
                for line in text.splitlines()
                if line.strip()
            ]

    elif file_type in ["jpg", "jpeg", "png"]:

        extraction_method = "ocr_image"
        text = extract_image_with_ocr(file_path)
        rows = [
            {"page": 1, "text": line}
            for line in text.splitlines()
            if line.strip()
        ]

    elif file_type == "docx":

        extraction_method = "docx_text"
        text = extract_docx(file_path)
        rows = [
            {"page": 1, "text": line}
            for line in text.splitlines()
            if line.strip()
        ]

    else:
        raise ValueError(
            f"Unsupported file type: {file_type}"
        )

    metadata = extract_metadata_from_rows(rows)
    medical_data = extract_medical_data(rows)

    document_metadata = {
        "source_file": Path(file_path).name,
        "file_type": file_type,
        "extraction_method": extraction_method
    }

    return create_canonical_report(
        metadata=metadata,
        medical_data=medical_data,
        document_metadata=document_metadata
    )


def save_parsed_report(
    file_path: str,
    output_directory: str = PARSED_REPORT_PATH
) -> str:
    """Parse one report and save its canonical JSON representation."""

    result = parse_report(file_path=file_path)
    os.makedirs(output_directory, exist_ok=True)

    output_file = os.path.join(
        output_directory,
        f"{Path(file_path).stem}.json"
    )

    with open(output_file, "w", encoding="utf-8") as json_file:
        json.dump(result, json_file, indent=2, ensure_ascii=False)

    return output_file


if __name__ == "__main__":

    for report in os.listdir(REPORT_PATH):

        f_name = os.path.join(REPORT_PATH, report)
        print(f"Processing {f_name}")
        output_file = save_parsed_report(f_name)

        print(f"Saved JSON: {output_file}")
