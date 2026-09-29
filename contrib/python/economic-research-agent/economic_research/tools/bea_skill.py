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

"""ADK Skill: Bureau of Economic Analysis (BEA). Regional & National GDP/Income."""

import json
import logging
import os
from typing import Any

import requests

from economic_research.shared_libraries.helper import (
    HTTP_TIMEOUT_SECONDS,
    get_session_api_key,
    redact_secrets,
    safe_error,
)

logger = logging.getLogger(__name__)

# report_type -> BEA Regional table/line. Aliases are matched lower-cased.
# CAGDP9 line 1: Real GDP (thousands of chained dollars).
# CAINC1 line 1: Personal income (thousands of dollars); line 3: per capita
# personal income (dollars).
_REPORTS = {
    "gdp": ("CAGDP9", "1", "Real GDP"),
    "real gdp": ("CAGDP9", "1", "Real GDP"),
    "personal income": ("CAINC1", "1", "Personal Income"),
    "income": ("CAINC1", "1", "Personal Income"),
    "per capita income": ("CAINC1", "3", "Per Capita Personal Income"),
    "per capita personal income": (
        "CAINC1",
        "3",
        "Per Capita Personal Income",
    ),
}

_UNIT_MULT_WORDS = {"0": "", "3": "Thousands of ", "6": "Millions of "}


def _to_number(value: Any) -> float | None:
    """Parses a BEA DataValue; '(NA)', '(D)', '(L)' etc. return None."""
    try:
        return float(str(value).replace(",", "").strip())
    except ValueError:
        return None


def _latest_numeric(entries: list[dict]) -> tuple[dict | None, str | None]:
    """Most recent entry with a numeric DataValue, plus a note if it is not
    the latest period (because the latest was suppressed or unavailable)."""
    ordered = sorted(entries, key=lambda e: str(e.get("TimePeriod", "")))
    if not ordered:
        return None, None
    latest_period = ordered[-1].get("TimePeriod")
    for entry in reversed(ordered):
        if _to_number(entry.get("DataValue")) is not None:
            note = None
            if entry.get("TimePeriod") != latest_period:
                note = (
                    f"Latest period {latest_period} is "
                    f"'{ordered[-1].get('DataValue')}' (not available or "
                    "suppressed); showing the most recent numeric year."
                )
            return entry, note
    return None, None


def _units(entry: dict, results: dict) -> str:
    """Unit label from CL_UNIT/UNIT_MULT (e.g. 'Thousands of dollars')."""
    unit = str(entry.get("CL_UNIT") or results.get("UnitOfMeasure") or "")
    mult = str(entry.get("UNIT_MULT", "")).strip()
    if not unit:
        return "units as reported by BEA"
    prefix = _UNIT_MULT_WORDS.get(mult, "")
    if prefix and not unit.lower().startswith(prefix.lower().strip()):
        return f"{prefix}{unit}"
    return unit


def _format_value(number: float, units: str) -> str:
    text = f"{number:,.0f}" if number.is_integer() else f"{number:,.2f}"
    return f"${text}" if "dollar" in units.lower() else text


def fetch_bea_regional_data(
    metro_names: list[str], report_type: str = "GDP"
) -> str:
    """
    Fetches regional economic data (GDP or Personal Income) directly from the BEA API.
    Essential for high-fidelity regional economic health assessments.

    report_type: "GDP" (real GDP, CAGDP9), "Personal Income" (CAINC1 line 1)
    or "Per Capita Income" (CAINC1 line 3).
    """
    report = _REPORTS.get((report_type or "GDP").strip().lower())
    if not report:
        return json.dumps(
            {
                "ERROR": (
                    f"Unsupported report_type '{report_type}'. Use 'GDP', "
                    "'Personal Income' or 'Per Capita Income'."
                )
            },
            indent=2,
        )
    table_name, line_code, metric_name = report

    h_key = (
        get_session_api_key("BEA_API_KEY", os.getenv("BEA_API_KEY")) or ""
    ).strip()
    bea_key = h_key.replace('"', "").replace("'", "")
    if not bea_key:
        return json.dumps(
            {"ERROR": "BEA_API_KEY not found in environment."}, indent=2
        )

    # MSA FIPS Registry (Hardened for Hub Comparisons)
    msa_fips = {
        "austin": "12420",
        "raleigh": "39580",
        "nashville": "34980",
        "san francisco": "41860",
        "dallas": "19100",
        "seattle": "42660",
        "houston": "26420",
        "denver": "19740",
        "miami": "33100",
    }

    try:
        results: list[dict[str, Any]] = []
        for city in metro_names:
            # Grounding: Clean names for robust mapping (handle 'MSA', 'TX', etc)
            city_clean = city.lower().replace(" msa", "").split(",")[0].strip()
            fips = msa_fips.get(city_clean)

            if not fips:
                results.append(
                    {
                        "City": city,
                        "Status": "MSA FIPS not found in Grounded Registry.",
                    }
                )
                continue

            # Live BEA API Call (Regional dataset, all available years)
            params = {
                "UserID": bea_key,
                "method": "GetData",
                "DataSetName": "Regional",
                "TableName": table_name,
                "GeoFIPS": fips,
                "LineCode": line_code,
                "Year": "ALL",
                "ResultFormat": "JSON",
            }
            response = requests.get(
                "https://apps.bea.gov/api/data",
                params=params,
                timeout=HTTP_TIMEOUT_SECONDS,
            )
            if response.status_code != 200:
                results.append(
                    {
                        "City": city,
                        "Status": f"BEA API Failure ({response.status_code})",
                    }
                )
                continue

            try:
                beaapi = response.json().get("BEAAPI", {})
                bea_results = beaapi.get("Results", {}) or {}
                if isinstance(bea_results, list):
                    bea_results = bea_results[0] if bea_results else {}
                api_error = bea_results.get("Error") or beaapi.get("Error")
                if api_error:
                    detail = (
                        api_error.get("APIErrorDescription", api_error)
                        if isinstance(api_error, dict)
                        else api_error
                    )
                    results.append(
                        {
                            "City": city,
                            "Status": "BEA API error: "
                            + redact_secrets(str(detail)),
                        }
                    )
                    continue

                entries = bea_results.get("Data", []) or []
                entry, note = _latest_numeric(entries)
                if entry:
                    units = _units(entry, bea_results)
                    number = _to_number(entry["DataValue"])
                    item = {
                        "City": city,
                        "Metric": f"{metric_name} ({units})",
                        "Value": (
                            _format_value(number, units)
                            if number is not None
                            else "N/A"
                        ),
                        "Units": units,
                        "Year": entry.get("TimePeriod"),
                        "Source": (
                            "Bureau of Economic Analysis (BEA) Live API "
                            f"({table_name} line {line_code})"
                        ),
                    }
                    if note:
                        item["Note"] = note
                    results.append(item)
                    continue

                # Fallback to FRED for MSA FIPS (GDP only; FRED has no
                # matching personal-income series in fetch_regional_macro_stats)
                if table_name == "CAGDP9" and _fred_gdp_fallback(
                    city, metric_name, results
                ):
                    continue

                results.append(
                    {
                        "City": city,
                        "Status": (
                            "No numeric data items in BEA response."
                            if entries
                            else "No data items in BEA response."
                        ),
                    }
                )
            except Exception as e:
                results.append(
                    {"City": city, "Status": f"Parsing Error: {safe_error(e)}"}
                )

        return json.dumps(results, indent=2)

    except Exception as e:
        return json.dumps({"ERROR": safe_error(e)}, indent=2)


def _fred_gdp_fallback(city: str, metric_name: str, results: list) -> bool:
    """Appends a FRED GDP row for ``city``; returns True on success."""
    from economic_research.tools.fred_skill import fetch_regional_macro_stats

    try:
        fred_res = fetch_regional_macro_stats([city], series_type="gdp")
        if "ERROR" in fred_res or "No FRED data" in fred_res:
            return False
        fred_data = json.loads(fred_res)
        if not fred_data:
            return False
        item = fred_data[0]
        results.append(
            {
                "City": city,
                # FRED series units vary; see the series ID in Source.
                "Metric": f"{metric_name} (units per FRED series)",
                "Value": item["Latest Value"],
                "Year": item["Latest Date"].split("-")[0],
                "Source": item["Source"] + " (BEA MSA Fallback)",
            }
        )
        return True
    except Exception as exc:
        logger.debug("FRED fallback failed for %s: %s", city, safe_error(exc))
        return False
