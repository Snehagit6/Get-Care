# backend/extractors/metadata_extractor.py

import re


METADATA_FIELDS = {
    "patient_name": [
        "patient name",
        "patient",
    ],

    "referred_by": [
        "referred by",
        "referred by doctor",
    ],

    "address": [
        "address",
    ],

    "tests_done": [
        "tests done",
        "test done",
        "tests",
    ],

    "processed_at": [
        "processed at",
    ],

    "report_date": [
        "report date",
        "collection date",
        "sample collection date",
        "date of collection",
        "collected on",
    ],
}


def normalize_label(text: str) -> str:
    text = text.lower()
    text = text.replace(":", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def find_metadata_label(row_text: str) -> tuple | None:

    normalized = normalize_label(row_text)

    for field, aliases in METADATA_FIELDS.items():

        for alias in aliases:

            if alias.lower() in normalized:
                return field, alias

    return None


def extract_inline_value(
    row_text: str,
    label: str
) -> str | None:

    pattern = (
        re.escape(label)
        + r"\s*:?\s*(.+)"
    )

    match = re.search(
        pattern,
        row_text,
        re.IGNORECASE
    )

    if not match:
        return None

    value = match.group(1).strip(" :-")

    return value if value else None


def extract_age_gender(
    patient_value: str
) -> tuple[int | None, str | None]:

    age = None
    gender = None

    # 62Y/F
    match = re.search(
        r"\b(\d{1,3})\s*Y\s*/\s*([MF])\b",
        patient_value,
        re.IGNORECASE
    )

    if match:
        age = int(match.group(1))
        gender = match.group(2).upper()
        return age, gender

    # 62Y / Female
    match = re.search(
        r"\b(\d{1,3})\s*(?:Y|YEARS?)\s*/\s*"
        r"(MALE|FEMALE|M|F)\b",
        patient_value,
        re.IGNORECASE
    )

    if match:
        age = int(match.group(1))

        raw_gender = match.group(2).upper()

        gender = {
            "MALE": "M",
            "FEMALE": "F",
            "M": "M",
            "F": "F"
        }.get(raw_gender)

        return age, gender

    return age, gender


def clean_patient_name(
    patient_value: str
) -> str:

    # Remove:
    # (62Y/F)
    # 62Y/F
    # (62 Years/Female)

    name = re.sub(
        r"\(?\s*\d{1,3}\s*"
        r"(?:Y|YEARS?)\s*/\s*"
        r"(?:M|F|MALE|FEMALE)\s*\)?",
        "",
        patient_value,
        flags=re.IGNORECASE
    )

    return name.strip(" :-")


def clean_metadata_value(
    value: str
) -> str:

    value = re.sub(r"\s+", " ", value)
    return value.strip()


def extract_metadata_from_rows(
    rows: list
) -> dict:

    metadata = {
        "patient_name": None,
        "age": None,
        "gender": None,
        "report_date": None,
        "referred_by": None,
        "address": None,
        "tests_done": [],
        "processed_at": None,
        "raw_metadata_rows": []
    }

    i = 0

    while i < len(rows):

        row_text = rows[i]["text"]

        match_result = find_metadata_label(
            row_text
        )

        if not match_result:
            i += 1
            continue

        field, matched_label = match_result

        value = extract_inline_value(
            row_text,
            matched_label
        )

        # Value may be on next row
        if not value and i + 1 < len(rows):

            next_text = rows[i + 1]["text"]

            if not find_metadata_label(next_text):
                value = next_text

        if value:

            value = clean_metadata_value(value)

            metadata["raw_metadata_rows"].append({
                "field": field,
                "page": rows[i]["page"],
                "source_row": row_text,
                "extracted_value": value
            })

            if field == "patient_name":

                age, gender = extract_age_gender(
                    value
                )

                metadata["patient_name"] = (
                    clean_patient_name(value)
                )

                metadata["age"] = age
                metadata["gender"] = gender

            elif field == "tests_done":

                metadata["tests_done"] = [
                    test.strip()
                    for test in re.split(
                        r"[,;/]",
                        value
                    )
                    if test.strip()
                ]

            elif field == "report_date":

                metadata["report_date"] = value

            else:

                metadata[field] = value

        i += 1

    return metadata