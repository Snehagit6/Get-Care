from __future__ import annotations

import json
from typing import Any


class DoctorWorkflow:

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

        evidence = [
            {
                "source": item.get(
                    "source"
                ),
                "document": item.get(
                    "document"
                ),
                "page": item.get(
                    "page"
                ),
                "text": item.get(
                    "text"
                )
            }
            for item in guidelines
        ]

        system_prompt = """
You are a clinical decision-support assistant
for a physician.

Use ONLY the supplied patient data, calculated trends
and retrieved guideline evidence.

Rules:
- Never invent patient values.
- Never invent guideline recommendations.
- Clearly distinguish observed facts from interpretation.
- State when information is missing.
- Do not autonomously diagnose or prescribe.
- Any treatment-related consideration must be framed
  for physician review.
- Cite guideline source and page when evidence is used.
"""

        user_prompt = f"""
Doctor question:
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

Retrieved guideline evidence:
{json.dumps(
    evidence,
    indent=2,
    ensure_ascii=False
)}

Generate:

1. Clinical summary
2. Key observed findings
3. Important longitudinal trends
4. Guideline-supported considerations
5. Missing information
6. Questions for clinician review
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
