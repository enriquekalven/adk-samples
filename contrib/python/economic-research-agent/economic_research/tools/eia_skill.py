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

"""ADK Skill: EIA Energy Data (U.S. Energy Information Administration)."""

import json
import logging
import os

import requests

from economic_research.shared_libraries.helper import (
    HTTP_TIMEOUT_SECONDS,
    get_session_api_key,
    safe_error,
)

# Configure basic logging
logger = logging.getLogger(__name__)


def _format_price(raw_price) -> str:
    """Formats an EIA price; null or non-numeric values become 'N/A'."""
    try:
        return f"{float(raw_price):.2f}"
    except (TypeError, ValueError):
        return "N/A"


def fetch_state_electricity_rates(
    state_codes: list[str], sector: str = "industrial"
) -> str:
    """
    Fetches real-time average electricity prices per kWh from the EIA Open Data API.
    Crucial for calculating the operational ROI of data centers or manufacturing plants.
    """
    h_eia_key = (
        get_session_api_key("EIA_API_KEY", os.getenv("EIA_API_KEY")) or ""
    ).strip()
    eia_key = h_eia_key.replace('"', "").replace("'", "")
    if not eia_key:
        return json.dumps(
            {"ERROR": "EIA_API_KEY not found in environment."}, indent=2
        )

    results = []
    # Map sector name to EIA v2 sectorid
    sector_map = {
        "industrial": "IND",
        "commercial": "COM",
        "residential": "RES",
    }
    s_id = sector_map.get(sector.lower(), "IND")

    for state in state_codes:
        state_clean = state.upper().strip()
        if len(state_clean) != 2 or not state_clean.isalpha():
            results.append(
                {
                    "State": state_clean,
                    "Status": (
                        "Invalid state code; expected a 2-letter postal "
                        "abbreviation (e.g. 'TX')."
                    ),
                }
            )
            continue
        url = (
            f"https://api.eia.gov/v2/electricity/retail-sales/data/?api_key={eia_key}"
            f"&frequency=monthly&data[0]=price"
            f"&facets[stateid][]={state_clean}"
            f"&facets[sectorid][]={s_id}"
            f"&sort[0][column]=period&sort[0][direction]=desc&length=1"
        )

        try:
            response = requests.get(url, timeout=HTTP_TIMEOUT_SECONDS)
            if response.status_code == 200:
                full_data = response.json()
                # EIA v2 often wraps data in 'response' -> 'data'
                data_list = full_data.get("response", {}).get("data", [])
                if not data_list:
                    # Fallback for alternative v2 structures or 'ALL' sectors
                    data_list = full_data.get("data", [])

                if data_list:
                    latest = data_list[0]
                    price = _format_price(latest.get("price"))
                    entry = {
                        "State": state_clean,
                        "Sector": sector.capitalize(),
                        "Avg Price (cents/kWh)": price,
                        "Period": latest.get("period", "Unknown"),
                        "Source": "U.S. Energy Information Administration (EIA v2)",
                    }
                    if price == "N/A":
                        entry["Note"] = (
                            "EIA reported no numeric price for this period."
                        )
                    results.append(entry)
                else:
                    results.append(
                        {
                            "State": state_clean,
                            "Status": "No specific sector data found.",
                        }
                    )
            else:
                results.append(
                    {
                        "State": state_clean,
                        "Status": f"EIA API failure ({response.status_code})",
                    }
                )
        except Exception as e:
            logger.warning("EIA request failed: %s", safe_error(e))
            results.append(
                {"State": state_clean, "Status": f"Error: {safe_error(e)}"}
            )

    if not results:
        return json.dumps(
            {"ERROR": f"No EIA data retrieved for {state_codes}"}, indent=2
        )

    return json.dumps(results, indent=2)
