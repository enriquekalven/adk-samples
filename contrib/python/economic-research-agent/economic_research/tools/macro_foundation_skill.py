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

"""ADK Skill: Macro Foundation (BEA & Census). Hardened macro benchmarks."""

import json
import os

from pydantic import BaseModel, Field

from economic_research.shared_libraries.helper import (
    SANDBOX_SOURCE,
    get_session_api_key,
)


class MacroRequest(BaseModel):
    state_names: list[str] = Field(
        ...,
        description="List of full state names to fetch BEA/Census data for.",
    )


def get_state_macro_health(state_names: list[str]) -> str:
    """
    Fetches GDP and Personal Income (BEA) along with Demographic shifts (Census) for states.
    This provides the 'Top-Line' economic context for site selection.

    NOTE: currently returns the same illustrative placeholder figures for
    every state (labelled as sandbox data); it does not call BEA/Census.
    Use fetch_bea_regional_data for live BEA figures.
    """
    bea_key = get_session_api_key("BEA_API_KEY", os.getenv("BEA_API_KEY"))
    if not bea_key:
        return "ERROR: BEA_API_KEY is missing."

    results = []

    for state in state_names:
        # 1. Fetch BEA State GDP (Sample Mapping logic)
        # In a full implementation, we would use the BEA 'GetDataSet' and 'GetData' endpoints.
        # This implementation uses the standardized BEA structure.

        # 2. Fetch Census Demographic benchmarks

        # (Simulating API successful return for demonstration of structural adherence)
        # Note: In production, we handle these requests with robust error handling.
        results.append(
            {
                "State": state,
                "Real GDP Growth (%)": "2.4% (Q3 2023)",
                "Personal Income (Per Capita)": "$68,540",
                "Population Shift (1-yr)": "+1.2%",
                "Note": (
                    "Placeholder values, identical for every state; not "
                    "state-specific BEA/Census data."
                ),
                "Source": SANDBOX_SOURCE,
            }
        )

    return json.dumps(results, indent=2)
