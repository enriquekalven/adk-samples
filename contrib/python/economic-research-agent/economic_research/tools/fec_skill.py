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
import logging
import os

import requests
from pydantic import BaseModel, Field

from economic_research.shared_libraries.helper import (
    get_session_api_key,
    safe_error,
)

logger = logging.getLogger(__name__)

FEC_REQUEST_TIMEOUT_SECONDS = 12
HIGH_POLITICAL_ACTIVITY_THRESHOLD = 50_000_000

# api.data.gov public key: works without registration but is heavily
# rate-limited, so results obtained with it are labelled as such.
FEC_DEMO_KEY = "DEMO_KEY"
DEMO_KEY_NOTE = (
    "FEC_API_KEY is not set; results were fetched with the public, heavily "
    "rate-limited api.data.gov DEMO_KEY. Set FEC_API_KEY for reliable access."
)

# 50 states, DC and the US territories FEC reports on.
VALID_FEC_STATES = frozenset(
    {
        "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
        "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
        "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
        "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
        "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
        "DC", "PR", "GU", "VI", "AS", "MP",
    }
)  # fmt: skip


class FECRequest(BaseModel):
    state_abbr: str = Field(
        ..., description="Two-letter state abbreviation (e.g., 'TX')."
    )
    cycle: str = Field("2024", description="Election cycle year to analyze.")


def _with_demo_note(payload: dict, using_demo_key: bool) -> str:
    if using_demo_key:
        payload["Note"] = DEMO_KEY_NOTE
    return json.dumps(payload, indent=2)


def analyze_political_stability(state_abbr: str, cycle: str = "2024") -> str:
    """
    Fetches Campaign Finance (FEC) contribution data for a specific state.
    Provides site selection agents with a metric for political stability and business alignment.
    High PAC activity often correlates with high regulatory engagement or a shifting political climate.
    """
    state = (state_abbr or "").strip().upper()
    if state not in VALID_FEC_STATES:
        return json.dumps(
            {
                "ERROR": (
                    f"Invalid state_abbr '{state_abbr}'. Expected a 2-letter "
                    "US state, DC or territory postal code (e.g. 'TX')."
                )
            },
            indent=2,
        )

    configured_key = (
        get_session_api_key("FEC_API_KEY", os.getenv("FEC_API_KEY")) or ""
    ).strip()
    key = configured_key or FEC_DEMO_KEY
    using_demo_key = not configured_key

    # FEC Endpoint: Contributions by State and Cycle
    url = "https://api.open.fec.gov/v1/totals/by_state/"
    params = {
        "api_key": key,
        "state": state,
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
                return _with_demo_note(
                    {"ERROR": f"No FEC data found for state: {state}"},
                    using_demo_key,
                )

            entry = results[0]
            try:
                receipts = float(entry.get("receipts") or 0)
            except (TypeError, ValueError):
                receipts = 0.0

            summary = {
                "State": state,
                "Election Cycle": cycle,
                "Total Contributions": f"${receipts:,.2f}",
                "Political Activity Level": "High"
                if receipts > HIGH_POLITICAL_ACTIVITY_THRESHOLD
                else "Moderate",
                "Source": "U.S. Federal Election Commission (FEC) API",
            }
            return _with_demo_note(summary, using_demo_key)
        else:
            return _with_demo_note(
                {"ERROR": f"FEC API status {response.status_code}"},
                using_demo_key,
            )

    except Exception as e:
        logger.warning("FEC request failed: %s", safe_error(e))
        return _with_demo_note({"ERROR": safe_error(e)}, using_demo_key)
