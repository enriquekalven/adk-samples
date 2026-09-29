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

"""ADK Skill: FRED Macro Data (St. Louis Fed). Replaces BigQuery with direct API calls."""

import json
import logging
import os

from pydantic import BaseModel, Field

from economic_research.shared_libraries.fred_client import (
    TimeoutFred as Fred,  # fredapi.Fred plus a request timeout
)
from economic_research.shared_libraries.helper import get_session_api_key


class FredRegionalRequest(BaseModel):
    city_names: list[str] = Field(
        ...,
        description="List of city names to fetch unemployment/macro data for.",
    )
    series_type: str = Field(
        "unemployment",
        description="Type of data to fetch: unemployment, gdp, or residential_construction.",
    )


def fetch_regional_macro_stats(
    city_names: list[str], series_type: str = "unemployment"
) -> str:
    """
    Fetches regional economic metrics directly from St. Louis Fed (FRED) API.
    Replaces legacy BigQuery labor tables. Support MSAs like Austin, Raleigh, etc.
    """
    fred_key = get_session_api_key("FRED_API_KEY", os.getenv("FRED_API_KEY"))
    if not fred_key:
        return "ERROR: FRED_API_KEY is not set in environment variables."

    fred = Fred(api_key=fred_key)

    # Simple mapping logic for top MSAs (Can be expanded with dynamic search)
    # Series IDs follow a pattern: [MSA CODE]UR for unemployment.
    msa_codes = {
        "Austin": "AUST448",  # Austin-Round Rock MSA
        "Raleigh": "RALE937",  # Raleigh-Cary MSA
        "San Francisco": "SANF806",
        "Dallas": "DALL148",
        "Denver": "DENN508",
        "Seattle": "SEAT653",
        "Atlanta": "ATLA013",
        "Charlotte": "CHAL837",
    }

    series_suffixes = {
        "unemployment": "UR",
        "gdp": "RGDP",  # Real GDP
        "residential_construction": "BP1FH",  # Building Permits 1-Unit
    }

    search_map = {
        "residential_construction": "building permits",
        "unemployment": "unemployment rate",
        "gdp": "real gdp",
    }

    def _search_series_id(city_name: str) -> str | None:
        """Top FRED search hit for the city + metric, or None.

        fredapi returns ``None`` (not an empty frame) when nothing matches.
        """
        query_topic = search_map.get(series_type, series_type)
        search_results = fred.search(f"{city_name} {query_topic}")
        if search_results is None or search_results.empty:
            return None
        return str(search_results.iloc[0].name)

    results = []

    for city in city_names:
        city_clean = city.split(",")[0].strip()  # Handle "Austin, TX"

        try:
            code = msa_codes.get(city_clean)
            if code:
                # Series construction logic: [MSA CODE] + metric suffix.
                suffix = series_suffixes.get(series_type, "UR")
                series_id = f"{code}{suffix}"
            else:
                # Plan B: search returns a complete series ID (no suffix).
                found_id = _search_series_id(city_clean)
                if not found_id:
                    continue
                series_id = found_id

            try:
                data_series = fred.get_series(series_id)
            except Exception:
                # If hard-coded ID fails, use search as fallback
                fallback_id = _search_series_id(city_clean)
                if not fallback_id or fallback_id == series_id:
                    continue
                series_id = fallback_id
                data_series = fred.get_series(series_id)

            if data_series is None:
                continue
            # FRED encodes missing observations as '.', which become NaN.
            data_series = data_series.dropna()

            if not data_series.empty:
                latest_val = data_series.iloc[-1]
                latest_date = data_series.index[-1].strftime("%Y-%m-%d")

                # Sample 10 annual data points (step by 12 for monthly data, or 1 for annual)
                historical_data = []
                step = (
                    12 if len(data_series) > 24 else 1
                )  # Simple heuristic: if monthly (len > 24), step by 12.
                subset = data_series.iloc[
                    -120::step
                ]  # Take last 120 points (e.g. 10 years of monthly data)

                for idx, val in subset.items():
                    historical_data.append(
                        {
                            "date": idx.strftime("%Y-%m-%d"),
                            "value": f"{val:.2f}%"
                            if "unemployment" in series_type
                            else f"{val:,.2f}",
                        }
                    )

                results.append(
                    {
                        "City": city_clean,
                        "Metric": series_type.capitalize(),
                        "Latest Value": f"{latest_val:.2f}%"
                        if "unemployment" in series_type
                        else f"{latest_val:,.2f}",
                        "Latest Date": latest_date,
                        "Historical_10_Year_Points": historical_data,
                        "Source": f"FRED ({series_id})",
                    }
                )
        except Exception as exc:
            logging.getLogger(__name__).debug(
                "FRED lookup failed for %s: %s", city, exc
            )
            continue

    if not results:
        return f"No FRED data found for the requested cities: {city_names}."

    # Return as JSON string for Scribe node processing
    return json.dumps(results, indent=2)
