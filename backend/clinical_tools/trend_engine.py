from __future__ import annotations

import sys
import json
from pathlib import Path
from typing import Any
from statistics import mean

sys.path.append(str(Path(__file__).parent.parent.parent))

from paths.path import PARSED_REPORT_PATH
from backend.clinical_tools.patient_timeline import (
    load_patient_timeline
)


class TrendEngine:
    """
    Deterministic longitudinal trend analysis.

    No LLM is used here.
    """

    def analyze(
        self,
        timeline: dict[str, Any]
    ) -> dict[str, Any]:

        lab_history = timeline.get(
            "lab_history",
            {}
        )

        trends: dict[
            str,
            dict[str, Any]
        ] = {}

        for metric, observations in lab_history.items():

            if len(observations) < 2:
                trends[metric] = {
                    "status": "insufficient_data",
                    "observations": len(observations)
                }
                continue

            trends[metric] = (
                self._analyze_metric(
                    observations
                )
            )

        return {
            "patient": timeline.get(
                "patient",
                {}
            ),
            "analysis": trends
        }

    # ---------------------------------------------------------
    # Metric analysis
    # ---------------------------------------------------------

    def _analyze_metric(
        self,
        observations: list[dict[str, Any]]
    ) -> dict[str, Any]:

        values = [
            float(item["value"])
            for item in observations
            if item.get("value") is not None
        ]

        if len(values) < 2:

            return {
                "status": "insufficient_data",
                "observations": len(values)
            }

        first = values[0]
        latest = values[-1]

        absolute_change = latest - first

        percentage_change = None

        if first != 0:
            percentage_change = (
                absolute_change / first
            ) * 100

        direction = self._direction(
            absolute_change
        )

        slope = self._calculate_slope(
            values
        )

        consistent_direction = (
            self._is_consistent_direction(
                values
            )
        )

        return {
            "status": "analyzed",

            "observations": len(values),

            "first": {
                "date": observations[0].get(
                    "date"
                ),
                "value": first
            },

            "latest": {
                "date": observations[-1].get(
                    "date"
                ),
                "value": latest
            },

            "minimum": min(values),

            "maximum": max(values),

            "mean": mean(values),

            "absolute_change": round(
                absolute_change,
                4
            ),

            "percentage_change": (
                round(
                    percentage_change,
                    2
                )
                if percentage_change is not None
                else None
            ),

            "direction": direction,

            "slope_per_observation": round(
                slope,
                4
            ),

            "consistent_direction": (
                consistent_direction
            ),

            "history": observations
        }

    # ---------------------------------------------------------
    # Direction
    # ---------------------------------------------------------

    @staticmethod
    def _direction(
        change: float
    ) -> str:

        tolerance = 1e-9

        if change > tolerance:
            return "increasing"

        if change < -tolerance:
            return "decreasing"

        return "stable"

    # ---------------------------------------------------------
    # Simple slope
    # ---------------------------------------------------------

    @staticmethod
    def _calculate_slope(
        values: list[float]
    ) -> float:

        n = len(values)

        if n < 2:
            return 0.0

        x = list(range(n))

        x_mean = mean(x)
        y_mean = mean(values)

        numerator = sum(
            (x[i] - x_mean)
            * (values[i] - y_mean)
            for i in range(n)
        )

        denominator = sum(
            (value - x_mean) ** 2
            for value in x
        )

        if denominator == 0:
            return 0.0

        return numerator / denominator

    # ---------------------------------------------------------
    # Consistency
    # ---------------------------------------------------------

    @staticmethod
    def _is_consistent_direction(
        values: list[float]
    ) -> bool:

        if len(values) < 3:
            return False

        differences = [
            values[index + 1]
            - values[index]
            for index in range(
                len(values) - 1
            )
        ]

        if all(
            difference >= 0
            for difference in differences
        ):
            return True

        if all(
            difference <= 0
            for difference in differences
        ):
            return True

        return False


def main() -> None:
    """Build a timeline from parsed reports and print its trends."""

    report_paths = sorted(
        Path(PARSED_REPORT_PATH).glob("*.json")
    )

    timeline = load_patient_timeline(
        reports=report_paths
    )

    trends = TrendEngine().analyze(
        timeline
    )

    print(
        json.dumps(
            trends,
            indent=2,
            ensure_ascii=False
        )
    )


if __name__ == "__main__":
    main()