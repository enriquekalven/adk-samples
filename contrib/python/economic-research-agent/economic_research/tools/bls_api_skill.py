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

from economic_research.shared_libraries.helper import (
    HTTP_TIMEOUT_SECONDS,
    get_session_api_key,
    redact_secrets,
    safe_error,
)
from economic_research.tools.dynamic_entity_resolver import (
    STATE_FIPS,
    STATE_NAMES,
)


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
            url,
            data=json.dumps(payload),
            headers=headers,
            timeout=HTTP_TIMEOUT_SECONDS,
        )
        if response.status_code == 200:
            data = response.json()

            # BLS returns success even if key is invalid, but status is REQUEST_NOT_PROCESSED
            if data.get("status") == "REQUEST_NOT_PROCESSED":
                msg = (data.get("message") or ["Unknown error"])[0]
                return json.dumps(
                    {"ERROR": f"BLS Request Failed: {redact_secrets(msg)}"},
                    indent=2,
                )

            results = []
            for series in data.get("Results", {}).get("series", []):
                series_id = series.get("seriesID")
                observations = series.get("data", [])

                latest_value = "N/A"
                status = "No data"
                if observations:
                    latest = observations[0]
                    raw_value = str(latest.get("value", "")).strip()
                    latest_value = f"{raw_value} ({latest.get('periodName')} {latest.get('year')})"
                    if _is_number(raw_value):
                        status = "Success"
                    else:
                        # BLS uses '-' or '(n)'-style markers for missing
                        # observations; do not report them as data.
                        latest_value = "N/A"

                results.append(
                    {
                        "Series ID": series_id,
                        "Current Value": latest_value,
                        "Status": status,
                        "Source": "U.S. Bureau of Labor Statistics (Live API)",
                    }
                )

            if not results:
                return json.dumps(
                    {"ERROR": f"BLS returned no series for {series_ids}."},
                    indent=2,
                )
            return json.dumps(results, indent=2)
        else:
            return json.dumps(
                {"ERROR": f"BLS API returned status {response.status_code}"},
                indent=2,
            )

    except Exception as e:
        return json.dumps({"ERROR": safe_error(e)}, indent=2)


def _is_number(value: str) -> bool:
    try:
        float(value.replace(",", ""))
    except ValueError:
        return False
    return True


def analyze_labor_force_quality(
    state_abbr: str, county_fips: str | None = None
) -> str:
    """
    Performs a comparative labor force assessment.

    Returns the latest BLS LAUS unemployment rate for a state (2-letter code
    or full name) or, when ``county_fips`` is given, for that county.
    """
    if county_fips:
        county = str(county_fips).strip()
        if not (county.isdigit() and len(county) == 5):
            return json.dumps(
                {"ERROR": f"Invalid 5-digit county FIPS: '{county_fips}'."},
                indent=2,
            )
        # Standard County Unemployment Series (20 chars):
        # LAUCN + 5-digit FIPS + 0000000003
        series_id = f"LAUCN{county}0000000003"
        return fetch_bls_series_data([series_id])

    state_key = (state_abbr or "").strip()
    abbr = state_key.upper()
    if abbr not in STATE_FIPS:
        abbr = next(
            (
                a
                for a, n in STATE_NAMES.items()
                if n.lower() == state_key.lower()
            ),
            "",
        )
    fips = STATE_FIPS.get(abbr)
    if not fips:
        return json.dumps(
            {
                "ERROR": (
                    f"Unknown state '{state_abbr}'. Use a 2-letter USPS "
                    "code (e.g. 'TX') or a full state name."
                )
            },
            indent=2,
        )
    # Statewide unemployment rate (20 chars): LASST + 2-digit FIPS +
    # 0000000000003, e.g. LASST480000000000003 for Texas.
    series_id = f"LASST{fips}0000000000003"
    return fetch_bls_series_data([series_id])
