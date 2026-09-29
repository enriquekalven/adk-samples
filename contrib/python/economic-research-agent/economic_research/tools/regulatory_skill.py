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

"""ADK Skill: Federal Register (Regulatory Risk tracking). Monitoring notices and rules."""

import json

import requests
from pydantic import BaseModel, Field


class RegulatoryRequest(BaseModel):
    state_names: list[str] = Field(
        ..., description="List of states to check for regulatory activities."
    )
    industry_topic: str = Field(
        "Semiconductor",
        description="Industry or topic to track (e.g. Energy, Zoning, Healthcare).",
    )


def fetch_regulatory_notices(
    state_names: list[str], industry_topic: str = "Semiconductor"
) -> str:
    """
    Fetches live regulatory filings from the Federal Register API.
    Essential for identifying legal risks and upcoming state policy shifts.
    """
    results = []

    for state in state_names:
        try:
            # Query Federal Register for the state + industry/topic
            # Example API: https://www.federalregister.gov/api/v1/documents.json
            query = f"{state} {industry_topic}"
            # params= URL-encodes the term, so topics like "Oil & Gas" survive.
            response = requests.get(
                "https://www.federalregister.gov/api/v1/documents.json",
                params={"conditions[term]": query, "per_page": 5},
                timeout=12,
            )
            if response.status_code == 200:
                data = response.json()
                filings = data.get("results") or []

                state_results = []
                for f in filings:
                    agencies = f.get("agency_names") or ["N/A"]
                    state_results.append(
                        {
                            "Title": f.get("title"),
                            "Action": f.get("action"),
                            "Date": f.get("publication_date"),
                            "URL": f.get("html_url"),
                            "Agency": agencies[0],
                        }
                    )

                results.append(
                    {
                        "State": state,
                        "Industry/Topic": industry_topic,
                        "Notices": state_results
                        if state_results
                        else "No recent filings found.",
                        "Source": "Federal Register (Live API)",
                    }
                )
            else:
                results.append(
                    {"State": state, "ERROR": f"Status {response.status_code}"}
                )
        except Exception as e:  # keep other states' results
            results.append(
                {
                    "State": state,
                    "ERROR": f"Federal Register lookup failed: {type(e).__name__}",
                }
            )

    return json.dumps(results, indent=2)
