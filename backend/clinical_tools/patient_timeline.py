from __future__ import annotations

import os
import sys
import json
from pathlib import Path
from typing import Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from paths.path import PARSED_REPORT_PATH

ReportSource = str | Path | dict[str, Any]


class PatientTimelineBuilder:
    """
    Combines canonical report JSON files into a single
    longitudinal patient timeline.

    This module is deterministic.
    No LLM is used here.
    """

    def __init__(self, reports: list[ReportSource]) -> None:
        self.reports = reports

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def build(self) -> dict[str, Any]:
        """
        Build a longitudinal patient timeline.

        Returns:
            {
                "patient": {...},
                "report_count": 3,
                "date_range": {...},
                "reports": [...],
                "lab_history": {...}
            }
        """

        reports = self._load_reports()

        if not reports:
            raise ValueError(
                "No canonical reports were found."
            )

        reports = self._sort_reports(reports)

        patient = self._validate_same_patient(
            reports
        )

        lab_history = self._build_lab_history(
            reports
        )

        return {
            "patient": patient,
            "report_count": len(reports),
            "date_range": {
                "start": reports[0].get(
                    "report_date"
                ),
                "end": reports[-1].get(
                    "report_date"
                )
            },
            "reports": reports,
            "lab_history": lab_history
        }

    # ---------------------------------------------------------
    # Loading
    # ---------------------------------------------------------

    def _load_reports(self) -> list[dict[str, Any]]:
        reports = []

        for report_source in self.reports:

            if isinstance(report_source, dict):
                reports.append(report_source)
                continue

            path = Path(report_source)

            if not path.exists():
                raise FileNotFoundError(
                    f"Canonical report not found: {path}"
                )

            with path.open(
                "r",
                encoding="utf-8"
            ) as file:

                report = json.load(file)

            reports.append(report)

        return reports

    # ---------------------------------------------------------
    # Sorting
    # ---------------------------------------------------------

    @staticmethod
    def _sort_reports(
        reports: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:

        return sorted(
            reports,
            key=lambda report: (
                report.get("report_date")
                or report.get(
                    "extraction_metadata",
                    {}
                ).get(
                    "report_date"
                )
                or ""
            )
        )

    # ---------------------------------------------------------
    # Patient validation
    # ---------------------------------------------------------

    @staticmethod
    def _validate_same_patient(
        reports: list[dict[str, Any]]
    ) -> dict[str, Any]:

        first_patient = reports[0].get(
            "patient",
            {}
        )

        patient_id = first_patient.get(
            "patient_id"
        )

        name = first_patient.get(
            "name"
        )

        age = first_patient.get(
            "age"
        )

        gender = first_patient.get(
            "gender"
        )

        for report in reports[1:]:

            current = report.get(
                "patient",
                {}
            )

            current_patient_id = current.get(
                "patient_id"
            )

            # If patient IDs are available,
            # use them as the strongest identifier.
            if (
                patient_id
                and current_patient_id
                and patient_id != current_patient_id
            ):
                raise ValueError(
                    "Reports appear to belong "
                    "to different patients."
                )

        return {
            "patient_id": patient_id,
            "name": name,
            "age": age,
            "gender": gender
        }

    # ---------------------------------------------------------
    # Lab history
    # ---------------------------------------------------------

    @staticmethod
    def _build_lab_history(
        reports: list[dict[str, Any]]
    ) -> dict[str, list[dict[str, Any]]]:

        history: dict[
            str,
            list[dict[str, Any]]
        ] = {}

        for report in reports:

            report_date = (
                report.get("report_date")
                or report.get(
                    "extraction_metadata",
                    {}
                ).get(
                    "report_date"
                )
            )

            results = report.get(
                "laboratory_results",
                []
            )

            for result in results:

                metric = result.get(
                    "canonical_name"
                )

                value = result.get(
                    "value"
                )

                if not metric or value is None:
                    continue

                history.setdefault(
                    metric,
                    []
                ).append(
                    {
                        "date": report_date,
                        "value": value,
                        "unit": result.get(
                            "unit"
                        ),
                        "reference_range": result.get(
                            "reference_range"
                        ),
                        "confidence": result.get(
                            "confidence"
                        )
                    }
                )

        return history


def load_patient_timeline(
    reports: list[ReportSource]
) -> dict[str, Any]:

    builder = PatientTimelineBuilder(
        reports
    )

    return builder.build()

if __name__ == "__main__":
    parsed_reports = sorted(
        PARSED_REPORT_PATH_PATH
        for PARSED_REPORT_PATH_PATH in Path(
            PARSED_REPORT_PATH
        ).glob("*.json")
    )
    print(load_patient_timeline(reports=parsed_reports))