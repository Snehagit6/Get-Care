import re


LAB_TEST_DEFINITIONS = {

    "hba1c": {
        "aliases": [
            "hba1c",
            "hba1 c",
            "hb a1c",
            "glycated hemoglobin",
            "glycated haemoglobin"
        ]
    },

    "estimated_average_glucose": {
        "aliases": [
            "estimated average glucose",
            "average blood glucose",
            "eag"
        ]
    },

    "total_cholesterol": {
        "aliases": [
            "total cholesterol",
            "serum cholesterol"
        ]
    },

    "hdl": {
        "aliases": [
            "hdl cholesterol - direct",
            "hdl cholesterol",
            "hdl-c",
            "high density lipoprotein"
        ]
    },

    "ldl": {
        "aliases": [
            "ldl cholesterol - direct",
            "ldl cholesterol",
            "ldl-c",
            "low density lipoprotein"
        ]
    },

    "triglycerides": {
        "aliases": [
            "triglycerides",
            "triglyceride"
        ]
    },

    "non_hdl_cholesterol": {
        "aliases": [
            "non-hdl cholesterol",
            "non hdl cholesterol"
        ]
    },

    "vldl": {
        "aliases": [
            "vldl cholesterol",
            "vldl"
        ]
    },

    "urine_microalbumin": {
        "aliases": [
            "urinary microalbumin",
            "urine microalbumin",
            "microalbumin"
        ]
    },

    "urine_creatinine": {
        "aliases": [
            "creatinine - urine",
            "urine creatinine",
            "urinary creatinine"
        ]
    },

    "urine_albumin_creatinine_ratio": {
        "aliases": [
            "ur. albumin/creatinine ratio",
            "albumin/creatinine ratio",
            "urine albumin creatinine ratio",
            "uacr"
        ]
    }
}


def normalize_text(
    text: str
) -> str:

    text = text.replace(
        "µ",
        "u"
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def find_test_in_text(
    text: str
) -> tuple | None:

    normalized = text.lower()

    for canonical_name, definition in (
        LAB_TEST_DEFINITIONS.items()
    ):

        for alias in definition["aliases"]:

            if alias.lower() in normalized:

                return (
                    canonical_name,
                    alias
                )

    return None


def extract_numbers(
    text: str
) -> list:

    numbers = re.findall(
        r"(?<![A-Za-z])\d+(?:\.\d+)?",
        text
    )

    values = []

    for number in numbers:

        try:
            values.append(
                float(number)
            )

        except ValueError:
            pass

    return values


def extract_unit(
    text: str
) -> str | None:

    normalized = (
        text.lower()
        .replace("µ", "u")
        .replace(" ", "")
    )

    unit_patterns = {

        "mg/dL": [
            "mg/dl",
            "mgdl"
        ],

        "g/dL": [
            "g/dl",
            "gdl"
        ],

        "µg/mL": [
            "ug/ml",
            "mcg/ml"
        ],

        "µg/mg": [
            "ug/mg",
            "mcg/mg"
        ],

        "mg/g": [
            "mg/g"
        ],

        "%": [
            "%"
        ],

        "mmol/L": [
            "mmol/l"
        ]
    }

    for canonical_unit, aliases in (
        unit_patterns.items()
    ):

        for alias in aliases:

            if alias in normalized:

                return canonical_unit

    return None


def extract_reference_range(
    text: str
) -> str | None:

    patterns = [

        r"[<>≤≥]\s*\d+(?:\.\d+)?",

        (
            r"\d+(?:\.\d+)?"
            r"\s*-\s*"
            r"\d+(?:\.\d+)?"
        )
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text
        )

        if match:

            return match.group(0)

    return None


def extract_value_near_test(
    canonical_name: str,
    alias: str,
    rows: list,
    start_index: int,
    window_size: int = 4
) -> float | None:
    """Extract the value associated with a test label, not its neighbors."""

    end_index = min(
        len(rows),
        start_index + window_size
    )

    alias_pattern = re.compile(
        re.escape(alias),
        re.IGNORECASE
    )

    for index in range(start_index, end_index):

        row_text = rows[index]["text"]
        match = alias_pattern.search(row_text)

        if not match:
            continue

        before_label = row_text[:match.start()]
        numbers_before_label = extract_numbers(before_label)

        if numbers_before_label:
            return numbers_before_label[-1]

        after_label = row_text[match.end():]
        value_match = re.search(
            r"(?<![A-Za-z<>≤≥])\d+(?:\.\d+)?"
            r"(?=\s*(?:%|[A-Za-z]|$))",
            after_label
        )

        if value_match:
            return float(value_match.group(0))

        if index + 1 < end_index:
            next_text = rows[index + 1]["text"].strip()
            next_value_match = re.fullmatch(
                r"(\d+(?:\.\d+)?)\s*"
                r"(?:%|mg\s*/?\s*d[Ll]|g\s*/?\s*d[Ll])?",
                next_text
            )
            if next_value_match:
                return float(next_value_match.group(1))

    return None


def collect_context(
    rows: list,
    start_index: int,
    window_size: int = 4
) -> str:
    """
    Collect nearby visual rows.

    This allows extraction when:
    test name, value and unit are
    in separate rows.
    """

    context_rows = []

    end_index = min(
        len(rows),
        start_index + window_size
    )

    for index in range(
        start_index,
        end_index
    ):

        context_rows.append(
            rows[index]["text"]
        )

    return " | ".join(
        context_rows
    )


def extract_test_from_context(
    canonical_name: str,
    alias: str,
    context: str,
    source_rows: list,
    rows: list,
    start_index: int
) -> dict | None:

    value = extract_value_near_test(
        canonical_name,
        alias,
        rows,
        start_index
    )

    if value is None:
        return None

    unit = extract_unit(
        context
    )

    reference_range = (
        extract_reference_range(context)
    )

    return {
        "canonical_name": canonical_name,
        "value": value,
        "unit": unit,
        "reference_range": reference_range,
        "source_rows": source_rows,
        "extraction_method": (
            "layout_aware_window_parser"
        ),
        "confidence": (
            "high"
            if unit
            else "medium"
        )
    }


def extract_medical_data(
    rows: list
) -> dict:
    """
    Extract medical tests from
    layout-reconstructed rows.
    """

    extracted_tests = []

    extracted_names = set()

    for index, row in enumerate(rows):

        row_text = row["text"]

        test_match = find_test_in_text(
            row_text
        )

        if not test_match:

            continue

        canonical_name, _ = test_match

        if canonical_name in extracted_names:

            continue

        context = collect_context(
            rows,
            start_index=index,
            window_size=4
        )

        source_rows = [
            rows[i]["text"]
            for i in range(
                index,
                min(index + 4, len(rows))
            )
        ]

        result = extract_test_from_context(
            canonical_name,
            test_match[1],
            context,
            source_rows,
            rows,
            index
        )

        if result:

            extracted_tests.append(
                result
            )

            extracted_names.add(
                canonical_name
            )

    return {
        "extracted_tests": extracted_tests,
        "extraction_summary": {
            "total_tests_extracted": len(
                extracted_tests
            ),
            "status": (
                "success"
                if extracted_tests
                else "no_tests_found"
            )
        }
    }