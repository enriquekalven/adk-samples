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

"""ADK Skill: Census ACS. Demographic & Educational Attainment."""

import json
import logging
import os

import requests

from economic_research.shared_libraries.helper import (
    HTTP_TIMEOUT_SECONDS,
    get_session_api_key,
    safe_error,
)

logger = logging.getLogger(__name__)

CENSUS_ACS_PROFILE_URL = "https://api.census.gov/data/2023/acs/acs1/profile"

# The Census API encodes "no estimate" annotations as large negative
# sentinels (e.g. -999999999, -888888888, -666666666, -555555555,
# -333333333, -222222222). A percentage can never be negative, so any
# negative value is treated as "not available".
_NOT_AVAILABLE = "N/A"


def _format_census_percentage(raw_value) -> tuple[str, str | None]:
    """Formats an ACS percentage, mapping sentinels/non-numerics to N/A.

    Returns:
        A ``(display_value, note)`` tuple. ``note`` explains why the value
        is N/A, or is ``None`` for a valid estimate.
    """
    try:
        value = float(raw_value)
    except (TypeError, ValueError):
        return _NOT_AVAILABLE, "Census returned a non-numeric estimate."
    if value < 0:
        return (
            _NOT_AVAILABLE,
            f"Census annotation value {raw_value} (estimate not available).",
        )
    return f"{raw_value}%", None


def _fetch_county_education(
    city_clean: str, full_fips: str, census_key: str
) -> dict:
    """Fetches one county. Errors are reported per city, never raised."""
    state_fips = full_fips[:2]
    county_fips = full_fips[2:]

    # Variables: DP02_0068E (Education Attainment - Bachelor's or Higher)
    # Dataset: ACS 1-Year Data Profiles (2022/2023)
    params = {
        "get": "NAME,DP02_0068PE",
        "for": f"county:{county_fips}",
        "in": f"state:{state_fips}",
        "key": census_key,
    }

    try:
        response = requests.get(
            CENSUS_ACS_PROFILE_URL, params=params, timeout=HTTP_TIMEOUT_SECONDS
        )
    except Exception as exc:
        logger.warning("Census request failed: %s", safe_error(exc))
        return {
            "City": city_clean,
            "Status": f"Census API request failed ({safe_error(exc)})",
        }

    if response.status_code != 200:
        return {
            "City": city_clean,
            "Status": f"Census API Failure ({response.status_code})",
        }

    try:
        data = response.json()
    except ValueError:
        # An invalid or unactivated key returns an HTML page with HTTP 200.
        return {
            "City": city_clean,
            "Status": (
                "Census API returned a non-JSON response (often an invalid "
                "or unactivated CENSUS_API_KEY)."
            ),
        }

    if not isinstance(data, list) or len(data) <= 1 or len(data[1]) < 2:
        return {"City": city_clean, "Status": "Census returned empty dataset."}

    row = data[1]
    name = row[0]
    value, note = _format_census_percentage(row[1])
    result = {
        "City": city_clean,
        "Geography": name,
        "Metric": "Bachelor's Degree or Higher (%)",
        "Value": value,
        "Source": "U.S. Census Bureau ACS (DP02 2023)",
    }
    if note:
        result["Note"] = note
    return result


def fetch_census_education_stats(city_names: list[str]) -> str:
    """
    Fetches real educational attainment statistics from the Census ACS API.
    Essential for talent-pipeline assessments in site selection.
    """
    c_key = (
        get_session_api_key("CENSUS_API_KEY", os.getenv("CENSUS_API_KEY")) or ""
    ).strip()
    census_key = c_key.replace('"', "").replace("'", "")
    if not census_key:
        return json.dumps(
            {"ERROR": "CENSUS_API_KEY not found in environment."}, indent=2
        )

    # Simplified Census County Mapping for Grounded Reliability
    # Format: [State FIPS][County FIPS]
    city_to_fips = {
        "austin": "48453",
        "raleigh": "37183",
        "seattle": "53033",
        "nashville": "47037",
        "denver": "08031",
    }

    try:
        results = []
        for city in city_names:
            city_clean = city.lower().split(",")[0].strip()
            full_fips = city_to_fips.get(city_clean)

            if not full_fips:
                results.append(
                    {
                        "City": city_clean,
                        "Status": "County FIPS mapping not found for Census API.",
                    }
                )
                continue

            results.append(
                _fetch_county_education(city_clean, full_fips, census_key)
            )

        return json.dumps(results, indent=2)

    except Exception as e:
        return json.dumps({"ERROR": safe_error(e)}, indent=2)
