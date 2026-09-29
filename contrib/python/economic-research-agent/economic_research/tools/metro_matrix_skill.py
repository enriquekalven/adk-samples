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

"""ADK Skill: Metro Matrix (2.2.1.1). Comprehensive MSA-level benchmarking."""

import json
import logging
from typing import Any

from economic_research.shared_libraries.helper import safe_error
from economic_research.tools.fred_skill import fetch_regional_macro_stats
from economic_research.tools.macro_foundation_skill import (
    get_state_macro_health,
)
from economic_research.tools.sentiment_skill import analyze_market_sentiment

logger = logging.getLogger(__name__)


def get_state_from_city(city: str) -> str:
    """Heuristic to map city names to their primary states."""
    lower_city = city.lower()
    if "," in city:
        return city.rsplit(",", maxsplit=1)[-1].strip()

    # Common Site Selection Hubs
    mapping = {
        "austin": "Texas",
        "dallas": "Texas",
        "houston": "Texas",
        "raleigh": "North Carolina",
        "durham": "North Carolina",
        "charlotte": "North Carolina",
        "nashville": "Tennessee",
        "memphis": "Tennessee",
        "denver": "Colorado",
        "boulder": "Colorado",
        "seattle": "Washington",
        "san francisco": "California",
        "atlanta": "Georgia",
        "phoenix": "Arizona",
    }

    for k, v in mapping.items():
        if k in lower_city:
            return v
    # Unknown: callers report "state unknown" rather than assume a state.
    return ""


def _load_json_list(raw: Any, label: str) -> list[dict]:
    """Parses a tool's JSON list output; error strings/dicts give []."""
    if not isinstance(raw, str) or not raw.strip().startswith("["):
        logger.info("%s unavailable: %s", label, str(raw)[:200])
        return []
    try:
        data = json.loads(raw)
    except ValueError:
        return []
    return [d for d in data if isinstance(d, dict)]


def generate_metro_matrix_report(city_names: list[str]) -> str:
    """
    Use this tool to generate a comprehensive 'Metro Matrix Report' (Scenario 2.2.1.1).
    """
    # 1. Gather Macro Health (BEA/Census)
    # Correct state derivation is critical for Live-API grounding accuracy.
    states = sorted(
        {s for s in (get_state_from_city(c) for c in city_names) if s}
    )
    macro_data: list[dict] = []
    if states:
        try:
            macro_data = _load_json_list(
                get_state_macro_health(states), "Macro data"
            )
        except Exception as e:
            logger.warning("Macro health lookup failed: %s", safe_error(e))

    # 2. Gather Labor Stats (Live FRED). fetch_regional_macro_stats returns
    # an error string (not JSON) on missing key / empty search results.
    labor_data: list[dict] = []
    try:
        labor_data = _load_json_list(
            fetch_regional_macro_stats(city_names, series_type="unemployment"),
            "FRED labor data",
        )
    except Exception as e:
        logger.warning("FRED labor lookup failed: %s", safe_error(e))

    # 3. Gather Business Climate Sentiment (Search/NewsAPI)
    sentiment_data = []
    for city in city_names:
        try:
            news = analyze_market_sentiment(
                f"{city} business climate Forbes Forbes 500"
            )
        except Exception as e:
            news = json.dumps({"ERROR": safe_error(e)})
        sentiment_data.append({"City": city, "Business Climate News": news})

    # 4. AI Synthesis: Consolidate into Matrix Structure
    matrix = []
    for i, city in enumerate(city_names):
        city_clean = city.split(",")[0].strip()
        state_target = get_state_from_city(city)

        # High-fidelity target matching (never another state's data)
        if not state_target:
            m_item = {"Message": f"State unknown for '{city}'; no macro data."}
        else:
            m_item = next(
                (
                    m
                    for m in macro_data
                    if str(m.get("State", "")).lower() == state_target.lower()
                ),
                {"Message": "No Macro Data"},
            )
        l_item = next(
            (
                labor
                for labor in labor_data
                if labor.get("City", "")
                and (
                    labor.get("City", "").lower() == city_clean.lower()
                    or labor.get("City", "").lower() in city.lower()
                )
            ),
            {"City": city_clean, "Message": "No Labor Data"},
        )
        s_item = sentiment_data[i]

        matrix.append(
            {
                "City": city,
                "Macro Context": m_item,
                "Labor Context": l_item,
                "Sentiment Summary": s_item["Business Climate News"],
                "Analysis Type": "Metro Matrix (2.2.1.1) Grounded Report",
            }
        )

    return json.dumps(matrix, indent=2)
