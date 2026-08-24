from __future__ import annotations

import json
from typing import Any


class PatientWorkflow:

    def __init__(
        self,
        llm
    ) -> None:

        self.llm = llm

    def reason(
        self,
        question: str,
        patient_profile: dict[str, Any],
        timeline: dict[str, Any],
        trends: dict[str, Any],
        guidelines: list[dict[str, Any]]
    ) -> str:

        system_prompt = """
You are a patient health education assistant
for a person with Type 2 diabetes.

Explain verified clinical information in simple language.

Rules:
- Do not invent values.
- Do not diagnose.
- Do not prescribe or change medication.
- Do not tell the patient to stop or start treatment.
- Do not replace the patient's clinician.
- Explain trends clearly and calmly.
- Encourage discussion with the treating clinician
  when medical review is appropriate.
"""

        user_prompt = f"""
Patient question:
{question}

Patient profile:
{json.dumps(
    patient_profile,
    indent=2,
    ensure_ascii=False
)}

Patient timeline:
{json.dumps(
    timeline,
    indent=2,
    ensure_ascii=False
)}

Calculated trends:
{json.dumps(
    trends,
    indent=2,
    ensure_ascii=False
)}

Relevant guideline evidence:
{json.dumps(
    [
        {
            "source": x.get("source"),
            "document": x.get("document"),
            "page": x.get("page"),
            "text": x.get("text")
        }
        for x in guidelines
    ],
    indent=2,
    ensure_ascii=False
)}

Explain the findings in patient-friendly language.
"""

        return self.llm.generate(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt.strip()
                },
                {
                    "role": "user",
                    "content": user_prompt.strip()
                }
            ]
        )