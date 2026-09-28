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

"""ADK Skill: Bureau of Labor Statistics (BLS). Employment & Unionization metrics."""

import json
import os

import requests

from economic_research.shared_libraries.helper import get_session_api_key


def fetch_bls_series_data(
    series_ids: list[str], start_year: str = "2023", end_year: str = "2024"
) -> str:
    """
    Fetches live labor statistics from the BLS (Bureau of Labor Statistics) API v2.
    """
    bls_key = (
        get_session_api_key("BLS_API_KEY", os.getenv("BLS_API_KEY")) or ""
    ).strip()
    url = "https://api.bls.gov/publicAPI/v2/timeseries/data/"

    headers = {"Content-type": "application/json"}
    payload = {
        "seriesid": series_ids,
        "startyear": start_year,
        "endyear": end_year,
    }

    if bls_key:
        payload["registrationkey"] = bls_key

    try:
        response = requests.post(
            url, data=json.dumps(payload), headers=headers, timeout=15
        )
        if response.status_code == 200:
            data = response.json()

            # BLS returns success even if key is invalid, but status is REQUEST_NOT_PROCESSED
            if data.get("status") == "REQUEST_NOT_PROCESSED":
                msg = data.get("message", ["Unknown error"])[0]
                return json.dumps(
                    {"ERROR": f"BLS Request Failed: {msg}"}, indent=2
                )

            results = []
            for series in data.get("Results", {}).get("series", []):
                series_id = series.get("seriesID")
                observations = series.get("data", [])

                latest_value = "N/A"
                if observations:
                    latest = observations[0]
                    latest_value = f"{latest.get('value')} ({latest.get('periodName')} {latest.get('year')})"

                results.append(
                    {
                        "Series ID": series_id,
                        "Current Value": latest_value,
                        "Status": "Success",
                        "Source": "U.S. Bureau of Labor Statistics (Live API)",
                    }
                )

            return json.dumps(results, indent=2)
        else:
            return json.dumps(
                {"ERROR": f"BLS API returned status {response.status_code}"},
                indent=2,
            )

    except Exception as e:
        return json.dumps({"ERROR": str(e)}, indent=2)


def analyze_labor_force_quality(
    state_abbr: str, county_fips: str | None = None
) -> str:
    """
    Performs a comparative labor force assessment.
    """
    if county_fips:
        # Standard County Unemployment Series: LAUCN + 5-digit FIPS + 03
        series_id = f"LAUCN{county_fips}0000000003"
        return fetch_bls_series_data([series_id])

    # State mapping dictionary (subset for top sites)
    state_fips_map = {
        "TX": "48",
        "NC": "37",
        "CA": "06",
        "TN": "47",
        "OH": "39",
        "WA": "53",
        "GA": "13",
    }

    fips = state_fips_map.get(state_abbr.upper(), "48")
    series_id = f"LASST{fips}000000000000003"
    return fetch_bls_series_data([series_id])
