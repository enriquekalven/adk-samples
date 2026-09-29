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

"""ADK Skill: USITC Trade Data. Regional Import/Export dependencies."""

import json
import logging
import os

import requests
from pydantic import BaseModel, Field

from economic_research.shared_libraries.helper import (
    HTTP_TIMEOUT_SECONDS,
    SANDBOX_SOURCE,
    get_session_api_key,
    safe_error,
)

logger = logging.getLogger(__name__)

# Census statehs month queried for live data. ALL_VAL_YR is year-to-date, so
# December gives the full-year total and every state shares one period.
TRADE_YTD_MONTH = "2024-12"


class TradeRequest(BaseModel):
    state_names: list[str] = Field(
        ..., description="List of states to fetch trade dependency data for."
    )
    commodity: str = Field(
        "Electronic Products",
        description="HS Code or Commodity name (e.g. 'Semiconductors', 'Auto parts').",
    )


HS_CODE_MAP = {
    "Electronic Products": "85",
    "Semiconductors": "85",
    "Electrical Machinery": "85",
    "Industrial Machinery": "84",
    "Machinery": "84",
    "Pharmaceuticals": "30",
    "Agricultural Products": "12",
}

STATE_MAP = {
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY",
}


def fetch_regional_trade_data(
    state_names: list[str], commodity: str = "Electronic Products"
) -> str:
    """
    Fetches international trade flow data for specific states and commodities.
    Essential for analyzing supply-chain resilience and industry clustering.
    """
    results = []
    census_key = (
        get_session_api_key("CENSUS_API_KEY", os.getenv("CENSUS_API_KEY")) or ""
    ).strip()

    # Normalize commodity name to handle case variations (e.g. "pharmaceuticals" -> "Pharmaceuticals")
    comm_clean = commodity.strip().title()

    # 1. Fallback Offline Data Bank
    trade_bank = {
        "Texas": {
            "Electronic Products": "Top Import (Mexico), $45B annual value",
            "Industrial Machinery": "$30B annual export",
        },
        "California": {
            "Electronic Products": "Global Hub, $60B annual flux",
            "Agricultural Products": "$15B annual export",
        },
        "North Carolina": {
            "Pharmaceuticals": "Major Manufacturing Hub, $8B annual export"
        },
        "Arizona": {
            "Semiconductors": "$12B annual state-origin export",
            "Electronic Products": "$12B annual state-origin export (Semiconductors)",
        },
    }

    # 2. Live API Sourcing
    if census_key:
        hs_code = HS_CODE_MAP.get(comm_clean)
        if hs_code:
            url = "https://api.census.gov/data/timeseries/intltrade/exports/statehs"
            params = {
                "get": "STATE,ALL_VAL_YR,E_COMMODITY",
                "E_COMMODITY": hs_code,
                # December's year-to-date value is the full-year total.
                "time": TRADE_YTD_MONTH,
                "key": census_key,
            }
            try:
                r = requests.get(
                    url, params=params, timeout=HTTP_TIMEOUT_SECONDS
                )
                if r.status_code == 200:
                    data = r.json()
                    live = _parse_statehs(data, state_names)
                    for state, (value_usd, time_period) in live.items():
                        if value_usd >= 1_000_000_000:
                            val_str = f"${value_usd / 1_000_000_000:.2f}B"
                        else:
                            val_str = f"${value_usd / 1_000_000:.2f}M"

                        results.append(
                            {
                                "State": state,
                                "Commodity": comm_clean,
                                "Market Profile": f"YTD Export Value: {val_str} (cumulative through {time_period})",
                                "Source": "U.S. Census Bureau International Trade API (statehs)",
                            }
                        )
                else:
                    logger.warning(
                        "Census trade API returned HTTP %s; falling back to "
                        "sandbox data.",
                        r.status_code,
                    )
            except Exception as e:
                logger.warning(
                    "Census trade API call failed (%s); falling back to "
                    "sandbox data.",
                    safe_error(e),
                )

    # 3. Apply offline fallback for any states that failed or weren't resolved live
    for state in state_names:
        if any(res.get("State") == state for res in results):
            continue

        data = trade_bank.get(state, {}).get(
            comm_clean,
            "Data unavailable in trade database.",
        )
        results.append(
            {
                "State": state,
                "Commodity": comm_clean,
                "Market Profile": data,
                "Source": f"{SANDBOX_SOURCE} - USITC-style regional trade profile",
            }
        )

    return json.dumps(results, indent=2)


def _state_abbr(state: str) -> str | None:
    """'Texas', 'texas' or 'TX' -> 'TX'."""
    cleaned = state.strip()
    if cleaned.upper() in STATE_MAP.values():
        return cleaned.upper()
    return STATE_MAP.get(cleaned.title())


def _parse_statehs(
    data: list[list[str]], state_names: list[str]
) -> dict[str, tuple[int, str]]:
    """Maps each requested state to (YTD export USD, month).

    Columns are located by header name (the Census API echoes predicate
    columns, so positions are not stable). If several months come back for a
    state, the latest month wins.
    """
    if not data or len(data) < 2:
        return {}
    header = [str(h).upper() for h in data[0]]
    try:
        state_idx = header.index("STATE")
        value_idx = header.index("ALL_VAL_YR")
    except ValueError:
        logger.warning("Unexpected Census statehs header: %s", data[0])
        return {}
    time_idx = header.index("TIME") if "TIME" in header else None

    live: dict[str, tuple[int, str]] = {}
    for state in state_names:
        abbr = _state_abbr(state)
        if not abbr:
            continue
        best: tuple[int, str] | None = None
        for row in data[1:]:
            if len(row) <= max(state_idx, value_idx):
                continue
            if str(row[state_idx]).strip().upper() != abbr:
                continue
            try:
                value = int(float(row[value_idx]))
            except (TypeError, ValueError):
                continue
            period = (
                str(row[time_idx])
                if time_idx is not None and len(row) > time_idx
                else TRADE_YTD_MONTH
            )
            if best is None or period > best[1]:
                best = (value, period)
        if best:
            live[state] = best
    return live
