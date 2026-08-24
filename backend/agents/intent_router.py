from __future__ import annotations

import json
from typing import Any


class IntentRouter:

    SYSTEM_PROMPT = """
You are the routing component of a diabetes clinical
decision-support application.

Determine which clinical tools are required to answer
the user's request.

Available tools:


1. patient_timeline
   Use when historical reports or chronological information
   is required.

2. trend_engine
   Use when the user asks about changes, progression,
   increase/decrease or trajectory.

3. guideline_rag
   Use when the user asks what ADA, WHO or IDF recommends,
   or when guideline evidence is needed to interpret a clinical
   question.

Choose only the tools necessary.

Return JSON only:

{
  "tools": [
    "patient_timeline",
    "trend_engine",
    "guideline_rag"
  ],
  "guideline_query": null
}
"""

    def build_request(
        self,
        question: str
    ) -> list[dict[str, str]]:

        return [
            {
                "role": "system",
                "content": self.SYSTEM_PROMPT.strip()
            },
            {
                "role": "user",
                "content": question
            }
        ]

    @staticmethod
    def parse_response(
        content: str
    ) -> dict[str, Any]:

        try:

            parsed = json.loads(
                content
            )

        except json.JSONDecodeError:

            return {
                "tools": [
                    "patient_timeline",
                    "trend_engine",
                    "guideline_rag"
                ],
                "guideline_query": content
            }

        return parsed
               