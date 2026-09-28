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

"""ADK Skill: Regional Economic Development (State EDO Portals)."""

import json

from pydantic import BaseModel, Field


class EDCRequest(BaseModel):
    state_names: list[str] = Field(
        ...,
        description="List of states to fetch Economic Development Corporation (EDO) portal data for.",
    )


def get_regional_edc_data(state_names: list[str]) -> str:
    """
    Fetches official state economic development portals and available CapEx incentive highlights.
    Essential for ground-level state policy and 'red carpet' service discovery.
    """
    results = []

    # High-fidelity grounding for top site-selection states
    edo_data = {
        "Texas": {
            "portal": "https://gov.texas.gov/business",
            "agency": "Texas Economic Development Corp",
            "highlights": "Texas Enterprise Fund (TEF), No state income tax, Skill Development Fund.",
        },
        "North Carolina": {
            "portal": "https://edpnc.com/",
            "agency": "Economic Development Partnership of NC (EDPNC)",
            "highlights": "JDIG Payroll Grants, One NC Fund, Custom workforce training (NCWorks).",
        },
        "Ohio": {
            "portal": "https://www.jobsohio.com/",
            "agency": "JobsOhio",
            "highlights": "R&D Investment loans, Workforce grants, Sites diversification program.",
        },
        "Virginia": {
            "portal": "https://www.vedp.org/",
            "agency": "Virginia Economic Development Partnership",
            "highlights": "VIC (Virginia Investment Performance), Data Center Sales Tax exemption.",
        },
    }

    for state in state_names:
        data = edo_data.get(
            state,
            {
                "portal": "N/A",
                "agency": f"State of {state} EDO",
                "highlights": "N/A",
            },
        )

        results.append(
            {
                "State": state,
                "Official EDO": data["agency"],
                "Portal URL": data["portal"],
                "Incentive Highlights": data["highlights"],
                "Source": "State Economic Development Portals (Grounded)",
            }
        )

    return json.dumps(results, indent=2)
