from __future__ import annotations

from typing import Any

from backend.clinical_tools.patient_timeline import (
    PatientTimelineBuilder,
    ReportSource
)

from backend.clinical_tools.trend_engine import (
    TrendEngine
)

from backend.clinical_tools.guideline_rag import (
    GuidelineRAG
)


class ClinicalToolkit:
    """
    Shared clinical tools used by both
    Doctor and Patient workflows.
    """

    def __init__(
        self,
        report_paths: list[ReportSource],
        rag: GuidelineRAG
    ) -> None:

        self.timeline_builder = (
            PatientTimelineBuilder(
                report_paths
            )
        )

        self.trend_engine = (
            TrendEngine()
        )

        self.guideline_rag = rag

        self.timeline = None
        self.trends = None

    # ---------------------------------------------------------
    # Patient Data Tool
    # ---------------------------------------------------------

    def get_patient_timeline(
        self
    ) -> dict[str, Any]:

        if self.timeline is None:

            self.timeline = (
                self.timeline_builder.build()
            )

        return self.timeline

    # ---------------------------------------------------------
    # Trend Tool
    # ---------------------------------------------------------

    def calculate_trends(
        self
    ) -> dict[str, Any]:

        if self.timeline is None:

            self.get_patient_timeline()

        if self.trends is None:

            self.trends = (
                self.trend_engine.analyze(
                    self.timeline
                )
            )

        return self.trends

    # ---------------------------------------------------------
    # Guideline Tool
    # ---------------------------------------------------------

    def retrieve_guidelines(
        self,
        query: str,
        top_k: int = 5
    ) -> list[dict[str, Any]]:

        return self.guideline_rag.retrieve(
            query=query,
            top_k=top_k
        )