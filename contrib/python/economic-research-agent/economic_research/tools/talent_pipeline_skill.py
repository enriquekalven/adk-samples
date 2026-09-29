# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""ADK Skill: Talent Pipeline & Innovation (IPEDS/USPTO). FutureProof site selection."""

import json

from pydantic import BaseModel, Field

from economic_research.shared_libraries.helper import SANDBOX_SOURCE


class TalentRequest(BaseModel):
    city_names: list[str] = Field(
        ...,
        description="List of city names to fetch talent pipeline benchmarks for.",
    )
    target_major: str = Field(
        "Computer Science",
        description="Target academic major pipeline to analyze.",
    )


def get_talent_pipeline_roi(
    city_names: list[str], target_major: str = "Computer Science"
) -> str:
    """
    Fetches IPEDS (Higher Ed) graduation numbers and USPTO (Patent) data.
    Companies move for tomorrow's graduates and innovation output.

    The figures are static, illustrative benchmarks (not live IPEDS/USPTO
    queries) and are not broken down by major: ``target_major`` is echoed in
    the output for context only and does not change the numbers.
    """
    results = []

    for city in city_names:
        city_clean = city.split(",")[0].strip().title()

        # IPEDS 2024 Graduation Trends (Sample data mapping)
        major_trends = {
            "Austin": {"grad_rate_3yr": "+12.4%", "patents": "1,240 (Yearly)"},
            "Raleigh": {"grad_rate_3yr": "+8.1%", "patents": "940 (Yearly)"},
            "San Francisco": {
                "grad_rate_3yr": "+5.2%",
                "patents": "4,820 (Yearly)",
            },
            "Seattle": {"grad_rate_3yr": "+9.8%", "patents": "3,410 (Yearly)"},
        }

        data = major_trends.get(
            city_clean, {"grad_rate_3yr": "N/A", "patents": "N/A"}
        )

        results.append(
            {
                "City": city_clean,
                "Major Pipeline": target_major,
                "Grad Rate Shift (3yr)": data["grad_rate_3yr"],
                "Annual Patent Output": data["patents"],
                "Note": (
                    "Illustrative all-major benchmarks; not specific to "
                    f"'{target_major}'."
                ),
                "Source": f"{SANDBOX_SOURCE} - IPEDS & USPTO-style benchmarks",
            }
        )

    return json.dumps(results, indent=2)
