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

"""ADK Skill: HUD Fair Market Rents (FMR). Talent Relocation & COLA."""

import json
import logging
import os

import requests

from economic_research.shared_libraries.helper import (
    get_session_api_key,
    safe_error,
)

# Configure simplified logging to capture API interactions
logger = logging.getLogger(__name__)


# HUD API key (JWT Bearer Token) resolved dynamically
def get_hud_api_key() -> str:
    h_raw = (
        get_session_api_key("HUD_API_KEY", os.getenv("HUD_API_KEY")) or ""
    ).strip()
    return h_raw.replace('"', "").replace("'", "")


CITY_TO_COUNTY_FIPS = {
    "austin": "48453",
    "raleigh": "37183",
    "dallas": "48113",
    "columbus": "39049",
    "nashville": "47037",
    "seattle": "53033",
    "denver": "08031",
    "phoenix": "04013",
    "boston": "25025",
    "atlanta": "13121",
    "charlotte": "37119",
    "orlando": "12095",
    "salt lake city": "49035",
    "richmond": "51760",
    "tampa": "12057",
    "houston": "48201",
    "miami": "12086",
    "las vegas": "32003",
    "portland": "41051",
    "detroit": "26163",
}


# (postal abbreviation, state FIPS, lower-case name) for 50 states + DC.
_STATES = (
    ("AL", "01", "alabama"), ("AK", "02", "alaska"),
    ("AZ", "04", "arizona"), ("AR", "05", "arkansas"),
    ("CA", "06", "california"), ("CO", "08", "colorado"),
    ("CT", "09", "connecticut"), ("DE", "10", "delaware"),
    ("DC", "11", "district of columbia"), ("FL", "12", "florida"),
    ("GA", "13", "georgia"), ("HI", "15", "hawaii"),
    ("ID", "16", "idaho"), ("IL", "17", "illinois"),
    ("IN", "18", "indiana"), ("IA", "19", "iowa"),
    ("KS", "20", "kansas"), ("KY", "21", "kentucky"),
    ("LA", "22", "louisiana"), ("ME", "23", "maine"),
    ("MD", "24", "maryland"), ("MA", "25", "massachusetts"),
    ("MI", "26", "michigan"), ("MN", "27", "minnesota"),
    ("MS", "28", "mississippi"), ("MO", "29", "missouri"),
    ("MT", "30", "montana"), ("NE", "31", "nebraska"),
    ("NV", "32", "nevada"), ("NH", "33", "new hampshire"),
    ("NJ", "34", "new jersey"), ("NM", "35", "new mexico"),
    ("NY", "36", "new york"), ("NC", "37", "north carolina"),
    ("ND", "38", "north dakota"), ("OH", "39", "ohio"),
    ("OK", "40", "oklahoma"), ("OR", "41", "oregon"),
    ("PA", "42", "pennsylvania"), ("RI", "44", "rhode island"),
    ("SC", "45", "south carolina"), ("SD", "46", "south dakota"),
    ("TN", "47", "tennessee"), ("TX", "48", "texas"),
    ("UT", "49", "utah"), ("VT", "50", "vermont"),
    ("VA", "51", "virginia"), ("WA", "53", "washington"),
    ("WV", "54", "west virginia"), ("WI", "55", "wisconsin"),
    ("WY", "56", "wyoming"),
)  # fmt: skip
_STATE_TO_FIPS = {abbr.lower(): fips for abbr, fips, _ in _STATES}
_STATE_TO_FIPS.update({name: fips for _, fips, name in _STATES})


def resolve_county_fips(input_str: str) -> str:
    """Maps a city name (optionally 'City, ST') to a 5-digit county FIPS.

    A trailing state ('Austin, TX' or 'Austin, Texas') is stripped and used
    to reject same-name cities in other states (e.g. 'Portland, ME' does not
    resolve to Portland, OR). Unknown inputs are returned unchanged
    (stripped) so callers can pass FIPS codes straight through.
    """
    raw = (input_str or "").strip()
    city, _, state = raw.partition(",")
    city = city.strip().lower()
    state = state.strip().lower().rstrip(".")
    expected_state_fips = _STATE_TO_FIPS.get(state) if state else None

    # Also accept MSA-style names such as 'Austin-Round Rock, TX'.
    candidates = [city]
    if "-" in city:
        candidates.append(city.split("-", maxsplit=1)[0].strip())

    for candidate in candidates:
        fips = CITY_TO_COUNTY_FIPS.get(candidate)
        if not fips:
            continue
        if expected_state_fips and not fips.startswith(expected_state_fips):
            logger.debug(
                "City %r is mapped to another state; not resolving %r.",
                candidate,
                raw,
            )
            return raw
        return fips
    return raw


def get_hud_entity_id(county_fips: str) -> str:
    """Standardize entity ID: Austin (48453) -> 4845399999."""
    if len(county_fips) == 5:
        return f"{county_fips}99999"
    return county_fips


def fetch_hud_fmr_data(county_fips: str) -> str:
    """
    Fetches HUD FMR with Title Case key matching for FY2026.

    Args:
        county_fips: 5-digit County FIPS code or common city name (e.g. "Austin", "Raleigh") as fallback.
    """
    api_key = get_hud_api_key()
    if not api_key:
        return json.dumps(
            {"ERROR": "HUD_API_KEY environment variable is empty."}, indent=2
        )

    county_fips = resolve_county_fips(county_fips)
    eid = get_hud_entity_id(county_fips)
    # FY2026 is currently active for MSAs like Austin
    for year in ["2026", "2025", "2024"]:
        try:
            url = f"https://www.huduser.gov/hudapi/public/fmr/data/{eid}?year={year}"
            headers = {"Authorization": f"Bearer {api_key}"}

            response = requests.get(url, headers=headers, timeout=12)

            if response.status_code == 200:
                full_payload = response.json()
                data_wrap = full_payload.get("data", {})
                basic = data_wrap.get("basicdata", {})
                # KEY: 'Two-Bedroom' (verified via network capture)
                rent = basic.get("Two-Bedroom") or basic.get("fmr_2")

                if rent:
                    return json.dumps(
                        {
                            "Geography": data_wrap.get(
                                "county_name", "Unknown"
                            ),
                            "Rent_2BR": f"${float(rent):,.0f}",
                            "Year": year,
                            "Source": f"HUD User API (FMR/{year})",
                        },
                        indent=2,
                    )
            elif response.status_code == 401:
                return json.dumps(
                    {
                        "ERROR": "HUD API Token Unauthorized (401). Check registration."
                    },
                    indent=2,
                )
        except Exception as exc:
            logger.debug(
                "HUD lookup failed for %s: %s", county_fips, safe_error(exc)
            )
            continue

    return json.dumps(
        {
            "ERROR": f"FMR lookup failed for FIPS {county_fips}. Verification required."
        },
        indent=2,
    )


# HUD sizes units at 1.5 persons per bedroom, so a 2-bedroom FMR unit is
# compared with the income limit of a 3-person household.
TWO_BEDROOM_HOUSEHOLD_SIZE = 3
_MAX_HUD_HOUSEHOLD_SIZE = 8


def fetch_hud_income_limits(county_fips: str, household_size: int = 1) -> str:
    """
    Fetches HUD Income Limits (AMI) with nested JSON schema matching.

    Args:
        county_fips: 5-digit County FIPS code or common city name (e.g. "Austin", "Raleigh") as fallback.
        household_size: Household size (1-8) for the 50% AMI (very low
            income) limit. Defaults to 1 person.
    """
    api_key = get_hud_api_key()
    if not api_key:
        return json.dumps(
            {"ERROR": "HUD_API_KEY empty or invalid format."}, indent=2
        )

    try:
        household_size = int(household_size)
    except (TypeError, ValueError):
        household_size = 0
    if not 1 <= household_size <= _MAX_HUD_HOUSEHOLD_SIZE:
        return json.dumps(
            {
                "ERROR": (
                    "household_size must be an integer between 1 and "
                    f"{_MAX_HUD_HOUSEHOLD_SIZE}."
                )
            },
            indent=2,
        )

    county_fips = resolve_county_fips(county_fips)
    eid = get_hud_entity_id(county_fips)
    for year in ["2025", "2024"]:
        try:
            url = f"https://www.huduser.gov/hudapi/public/il/data/{eid}?year={year}"
            headers = {"Authorization": f"Bearer {api_key}"}

            response = requests.get(url, headers=headers, timeout=12)

            if response.status_code == 200:
                payload = response.json().get("data", {})
                # SCHEMA: Very Low Income (50% AMI) is stored in 'very_low'
                very_low = payload.get("very_low", {})
                # Key: 'il50_p1' for 1-person ... 'il50_p8' for 8-person.
                # Legacy payloads use 'il_data' -> 'il50_<n>'.
                income = very_low.get(f"il50_p{household_size}") or payload.get(
                    "il_data", {}
                ).get(f"il50_{household_size}")

                if income:
                    return json.dumps(
                        {
                            "Geography": payload.get("county_name", "Unknown"),
                            "AMI_50_Level": f"${float(income):,.0f}",
                            "Household_Size": household_size,
                            "Year": year,
                            "Source": f"HUD User API (IL/{year})",
                        },
                        indent=2,
                    )
        except Exception as exc:
            logger.debug(
                "HUD lookup failed for %s: %s", county_fips, safe_error(exc)
            )
            continue

    return json.dumps(
        {"ERROR": f"Income Limit lookup failed for FIPS {county_fips}."},
        indent=2,
    )


def analyze_housing_affordability(county_fips: str) -> str:
    """
    Consolidated site-selection affordability report.

    Compares the 2-bedroom Fair Market Rent with the 50% AMI income limit
    for a 3-person household (HUD's 1.5 persons-per-bedroom convention).

    Args:
        county_fips: 5-digit County FIPS code or common city name (e.g. "Austin", "Raleigh") as fallback.
    """
    fmr = json.loads(fetch_hud_fmr_data(county_fips))
    il = json.loads(
        fetch_hud_income_limits(
            county_fips, household_size=TWO_BEDROOM_HOUSEHOLD_SIZE
        )
    )

    if "ERROR" in fmr or "ERROR" in il:
        return json.dumps(
            {
                "ERROR": f"HUD Analytics Pipeline Broken: {fmr.get('ERROR', '')} {il.get('ERROR', '')}"
            },
            indent=2,
        )

    try:
        r_val = float(fmr["Rent_2BR"].replace("$", "").replace(",", ""))
        i_val = float(il["AMI_50_Level"].replace("$", "").replace(",", ""))
        # 50% AMI Threshold check
        monthly_income = i_val / 12
        burden_pct = (r_val / monthly_income) * 100

        verdict = (
            "Severely Burdened"
            if burden_pct > 50
            else "High Cost"
            if burden_pct > 30
            else "Optimal"
        )

        return json.dumps(
            {
                "Geography": fmr["Geography"],
                "Analysis": (
                    "Housing Affordability: 2BR FMR vs. 50% AMI "
                    f"({TWO_BEDROOM_HOUSEHOLD_SIZE}-person household)"
                ),
                "FMR_Rent_2BR": fmr["Rent_2BR"],
                "Monthly_Income_50_AMI": f"${monthly_income:,.2f}",
                "Household_Size_Basis": (
                    f"{TWO_BEDROOM_HOUSEHOLD_SIZE} persons (HUD convention of "
                    "1.5 persons per bedroom for a 2-bedroom unit)"
                ),
                "Rent_to_Income_Ratio": f"{burden_pct:.1f}%",
                "Site_Selection_Verdict": verdict,
                "Source": f"Grounded HUD Analytics (FMR:{fmr['Year']}/IL:{il['Year']})",
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps(
            {"ERROR": f"Calculation error: {safe_error(e)}"}, indent=2
        )


def fetch_hud_usps_crosswalk(zip_code: str) -> str:
    """
    Queries HUD USPS crosswalk API to map ZIP code to County FIPS code (type=2).

    Args:
        zip_code: A 5-digit numeric ZIP code string (e.g. "78702").
    """
    zip_code = zip_code.strip()
    if not zip_code.isdigit() or len(zip_code) != 5:
        return json.dumps(
            {
                "ERROR": f"Invalid 5-digit numeric ZIP code: {zip_code}. City names are not supported by this tool."
            },
            indent=2,
        )

    api_key = get_hud_api_key()
    if not api_key:
        return json.dumps(
            {"ERROR": "HUD_API_KEY environment variable is empty."}, indent=2
        )

    try:
        url = f"https://www.huduser.gov/hudapi/public/usps?type=2&query={zip_code}"
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(url, headers=headers, timeout=12)

        if response.status_code == 200:
            payload = response.json()
            results = payload.get("data", {}).get("results", [])
            if results:
                # Find the county with the highest residential ratio
                best_match = max(
                    results, key=lambda x: float(x.get("res_ratio", 0))
                )
                county_fips = best_match.get("geoid")
                return json.dumps(
                    {
                        "ZIP": zip_code,
                        "County_FIPS": county_fips,
                        "Residential_Ratio": best_match.get("res_ratio"),
                        "Source": "HUD User USPS Crosswalk API",
                    },
                    indent=2,
                )
    except Exception as e:
        return json.dumps(
            {"ERROR": f"USPS Crosswalk lookup failed: {safe_error(e)}"},
            indent=2,
        )

    return json.dumps(
        {"ERROR": f"No FIPS mapping found for ZIP code {zip_code}."}, indent=2
    )


def fetch_hud_chas_data(county_fips: str) -> str:
    """
    Queries HUD CHAS API for housing problem and cost burden statistics.

    Args:
        county_fips: 5-digit County FIPS code or common city name (e.g. "Austin", "Raleigh") as fallback.
    """
    api_key = get_hud_api_key()
    if not api_key:
        return json.dumps(
            {"ERROR": "HUD_API_KEY environment variable is empty."}, indent=2
        )

    county_fips = resolve_county_fips(county_fips)
    # resolve_county_fips passes unknown names through unchanged, so a
    # 5-letter city name (e.g. "Tulsa") would otherwise reach int() below.
    if len(county_fips) != 5 or not county_fips.isdigit():
        return json.dumps(
            {
                "ERROR": (
                    f"Invalid 5-digit County FIPS code: {county_fips}. "
                    "Resolve the county first (e.g. with "
                    "fetch_hud_usps_crosswalk for a ZIP code)."
                )
            },
            indent=2,
        )

    state_id = int(county_fips[:2])
    entity_id = county_fips[2:]

    for year in ["2018-2022", "2017-2021", "2016-2020"]:
        try:
            url = (
                f"https://www.huduser.gov/hudapi/public/chas"
                f"?type=3&stateId={state_id}&entityId={entity_id}&year={year}"
            )
            headers = {"Authorization": f"Bearer {api_key}"}
            response = requests.get(url, headers=headers, timeout=12)

            if response.status_code == 200:
                results = response.json()
                if not results:
                    continue
                payload = results[0]

                total_households = float(payload.get("A18") or 0)
                problems_count = float(payload.get("B3") or 0)
                cost_burden_30_50 = float(payload.get("D6") or 0)
                cost_burden_50 = float(payload.get("D9") or 0)
                cost_burden_count = cost_burden_30_50 + cost_burden_50

                problems_pct = (
                    (problems_count / total_households * 100)
                    if total_households
                    else 0
                )
                cost_burden_pct = (
                    (cost_burden_count / total_households * 100)
                    if total_households
                    else 0
                )

                return json.dumps(
                    {
                        "Geography": payload.get("geoname", "Unknown"),
                        "Total_Households": f"{int(total_households):,}",
                        "Households_With_Housing_Problems_Pct": f"{problems_pct:.1f}%",
                        "Households_Cost_Burdened_Pct": f"{cost_burden_pct:.1f}%",
                        "Year": year,
                        "Source": f"HUD User CHAS API ({year})",
                    },
                    indent=2,
                )
        except Exception as exc:
            logger.debug(
                "HUD lookup failed for %s: %s", county_fips, safe_error(exc)
            )
            continue

    return json.dumps(
        {"ERROR": f"CHAS lookup failed for FIPS {county_fips}."}, indent=2
    )
