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

"""ADK Skill: Political Stability & Campaign Finance (FEC API)."""

import json
import os

import requests
from pydantic import BaseModel, Field

from economic_research.shared_libraries.helper import get_session_api_key

FEC_REQUEST_TIMEOUT_SECONDS = 12
HIGH_POLITICAL_ACTIVITY_THRESHOLD = 50_000_000


class FECRequest(BaseModel):
    state_abbr: str = Field(
        ..., description="Two-letter state abbreviation (e.g., 'TX')."
    )
    cycle: str = Field("2024", description="Election cycle year to analyze.")


def analyze_political_stability(state_abbr: str, cycle: str = "2024") -> str:
    """
    Fetches Campaign Finance (FEC) contribution data for a specific state.
    Provides site selection agents with a metric for political stability and business alignment.
    High PAC activity often correlates with high regulatory engagement or a shifting political climate.
    """
    key = (
        get_session_api_key("FEC_API_KEY", os.getenv("FEC_API_KEY")) or ""
    ).strip() or "DEMO_KEY"

    # FEC Endpoint: Contributions by State and Cycle
    url = "https://api.open.fec.gov/v1/totals/by_state/"
    params = {
        "api_key": key,
        "state": state_abbr,
        "cycle": cycle,
        "per_page": 1,
    }

    try:
        response = requests.get(
            url, params=params, timeout=FEC_REQUEST_TIMEOUT_SECONDS
        )
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])

            if not results:
                return json.dumps(
                    {"ERROR": f"No FEC data found for state: {state_abbr}"},
                    indent=2,
                )

            entry = results[0]

            summary = {
                "State": state_abbr,
                "Election Cycle": cycle,
                "Total Contributions": f"${entry.get('receipts', 0):,.2f}",
                "Political Activity Level": "High"
                if entry.get("receipts", 0) > HIGH_POLITICAL_ACTIVITY_THRESHOLD
                else "Moderate",
                "Source": "U.S. Federal Election Commission (FEC) API",
            }
            return json.dumps(summary, indent=2)
        else:
            return json.dumps(
                {"ERROR": f"FEC API status {response.status_code}"}, indent=2
            )

    except Exception as e:
        return json.dumps({"ERROR": str(e)}, indent=2)
