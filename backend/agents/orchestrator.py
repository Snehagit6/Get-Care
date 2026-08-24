from __future__ import annotations

from typing import Any

from backend.agents.intent_router import (
    IntentRouter
)

from backend.workflows.doctor_workflow import (
    DoctorWorkflow
)

from backend.workflows.patient_workflow import (
    PatientWorkflow
)


class AgentOrchestrator:

    def __init__(
        self,
        toolkit,
        llm
    ) -> None:

        self.toolkit = toolkit

        self.llm = llm

        self.router = IntentRouter()

        self.doctor_workflow = (
            DoctorWorkflow(llm)
        )

        self.patient_workflow = (
            PatientWorkflow(llm)
        )

    def run(
        self,
        question: str,
        role: str
    ) -> dict[str, Any]:

        # -------------------------------------------------
        # 1. Intent routing
        # -------------------------------------------------

        route_response = self.llm.generate(
            messages=(
                self.router.build_request(
                    question
                )
            ),
            temperature=0.0,
            max_completion_tokens=1000
        )

        route = (
            self.router
            .parse_response(
                route_response
            )
        )

        requested_tools = set(
            route.get(
                "tools",
                []
            )
        )

        # -------------------------------------------------
        # 2. Timeline
        # -------------------------------------------------

        timeline = None

        if (
            "patient_timeline"
            in requested_tools
            or
            "trend_engine"
            in requested_tools
            or
            "guideline_rag"
            in requested_tools
        ):

            timeline = (
                self.toolkit
                .get_patient_timeline()
            )

        # -------------------------------------------------
        # 3. Trends
        # -------------------------------------------------

        trends = None

        if (
            "trend_engine"
            in requested_tools
        ):

            trends = (
                self.toolkit
                .calculate_trends()
            )

        # -------------------------------------------------
        # 4. Guidelines
        # -------------------------------------------------

        guidelines = []

        if (
            "guideline_rag"
            in requested_tools
        ):

            guideline_query = (
                route.get(
                    "guideline_query"
                )
                or question
            )

            guidelines = (
                self.toolkit
                .retrieve_guidelines(
                    query=guideline_query,
                    top_k=5
                )
            )

        # -------------------------------------------------
        # 5. Fill missing context needed
        # by reasoning workflow
        # -------------------------------------------------

        if timeline is None:

            timeline = (
                self.toolkit
                .get_patient_timeline()
            )

        patient_profile = timeline.get(
            "patient",
            {}
        )

        if trends is None:

            trends = {
                "status": (
                    "not_requested"
                )
            }

        # -------------------------------------------------
        # 6. Role-specific reasoning
        # -------------------------------------------------

        if role.lower() == "doctor":

            answer = (
                self.doctor_workflow
                .reason(
                    question=question,
                    patient_profile=(
                        patient_profile
                    ),
                    timeline=timeline,
                    trends=trends,
                    guidelines=guidelines
                )
            )

        elif role.lower() == "patient":

            answer = (
                self.patient_workflow
                .reason(
                    question=question,
                    patient_profile=(
                        patient_profile
                    ),
                    timeline=timeline,
                    trends=trends,
                    guidelines=guidelines
                )
            )

        else:

            raise ValueError(
                "role must be "
                "'doctor' or 'patient'"
            )

        return {
            "role": role,
            "question": question,
            "route": route,
            "patient_profile": patient_profile,
            "timeline": timeline,
            "trends": trends,
            "guidelines": guidelines,
            "answer": answer
        }