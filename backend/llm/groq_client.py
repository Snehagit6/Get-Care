from __future__ import annotations

import json
import os
from typing import Any

from groq import Groq


class GroqLLM:

    def __init__(
        self,
        model: str = "openai/gpt-oss-20b"
    ) -> None:

        api_key = os.getenv(
            "GROQ_API_KEY"
        )

        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set."
            )

        self.client = Groq(
            api_key=api_key
        )

        self.model = model

    def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_completion_tokens: int = 4096
    ) -> str:

        response = (
            self.client
            .chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_completion_tokens=(
                    max_completion_tokens
                ),
                reasoning_effort="medium",
                stream=False
            )
        )

        return (
            response
            .choices[0]
            .message
            .content
            or ""
        )

    def generate_json(
        self,
        messages: list[dict[str, str]],
        schema: dict[str, Any],
        schema_name: str,
        temperature: float = 0.2
    ) -> dict[str, Any]:

        response = (
            self.client
            .chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_completion_tokens=4096,
                reasoning_effort="medium",
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": schema_name,
                        "strict": True,
                        "schema": schema
                    }
                },
                stream=False
            )
        )

        content = (
            response
            .choices[0]
            .message
            .content
        )

        return json.loads(
            content or "{}"
        )