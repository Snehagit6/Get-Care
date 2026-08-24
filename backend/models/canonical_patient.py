# backend/models/canonical_patient.py

from datetime import datetime


def create_canonical_report(
    metadata: dict,
    medical_data: dict,
    document_metadata: dict
) -> dict:

    report_date = metadata.get(
        "report_date"
    )

    patient_name = metadata.get(
        "patient_name"
    )

    age = metadata.get(
        "age"
    )

    gender = metadata.get(
        "gender"
    )

    return {

        "schema_version": "1.0",

        "report_id": (
            f"{patient_name or 'UNKNOWN'}_"
            f"{report_date or 'UNKNOWN'}"
        ),

        # IMPORTANT:
        # report_date is top-level because
        # PatientTimeline needs it.
        "report_date": report_date,

        "patient": {

            "patient_id": None,

            "name": patient_name,

            "age": age,

            "gender": gender
        },

        "report_metadata": {

            "referred_by": metadata.get(
                "referred_by"
            ),

            "address": metadata.get(
                "address"
            ),

            "tests_done": metadata.get(
                "tests_done",
                []
            ),

            "processed_at": metadata.get(
                "processed_at"
            )
        },

        "laboratory_results": (
            medical_data.get(
                "extracted_tests",
                []
            )
        ),

        "extraction_metadata": {

            "created_at": (
                datetime.utcnow()
                .isoformat()
            ),

            **document_metadata,

            "total_tests_extracted": (
                medical_data
                .get(
                    "extraction_summary",
                    {}
                )
                .get(
                    "total_tests_extracted",
                    0
                )
            )
        }
    }