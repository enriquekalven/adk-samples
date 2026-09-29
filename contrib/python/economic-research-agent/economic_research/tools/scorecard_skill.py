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

"""ADK Skill: Multi-Variable Location Scorecard for Site Selection."""

import json
import logging
import re
from typing import Any

from economic_research.shared_libraries.helper import safe_error
from economic_research.tools.bls_api_skill import analyze_labor_force_quality
from economic_research.tools.eia_skill import fetch_state_electricity_rates
from economic_research.tools.tax_foundation_skill import fetch_state_tax_rates

logger = logging.getLogger(__name__)

# States with no corporate income tax (Tax Foundation, 2024). OH, TX, WA and
# NV levy gross receipts taxes instead, which a 0% income-tax rate does not
# capture; SD and WY levy neither.
NO_CORPORATE_INCOME_TAX = {
    "TX": "gross receipts tax (franchise 'margin' tax) applies",
    "OH": "gross receipts tax (Commercial Activity Tax) applies",
    "WA": "gross receipts tax (Business & Occupation tax) applies",
    "NV": "gross receipts tax (Commerce Tax) applies",
    "SD": "no gross receipts tax",
    "WY": "no gross receipts tax",
}

# Used only when no candidate state has data for a criterion (all states
# then tie on it). Labelled "default assumption" in the output.
_LAST_RESORT_DEFAULTS = {
    "corporate_tax": 6.0,  # % top marginal rate
    "electricity_rate": 10.0,  # cents/kWh
    "labor_quality_index": 4.0,  # % unemployment rate
}

_NUMBER = re.compile(r"-?\d+(?:\.\d+)?")


def _parse_number(raw: Any) -> float | None:
    """First number in ``raw`` ('7.85', '7.85 ¢/kWh', '3.9 (Aug 2025)')."""
    if raw is None:
        return None
    match = _NUMBER.search(str(raw).replace(",", ""))
    return float(match.group(0)) if match else None


def _parse_corporate_tax(raw: Any) -> float | None:
    """Top marginal rate from Tax Foundation text; 'None…' means 0%."""
    if raw is None:
        return None
    text = str(raw).strip()
    lower = text.lower()
    if lower.startswith("none") or "no corporate income tax" in lower:
        return 0.0
    rates = [float(m) for m in re.findall(r"(\d+(?:\.\d+)?)\s*%", text)]
    return max(rates) if rates else None


def _tax_rate(st_code: str, st_name: str) -> tuple[float | None, str]:
    if st_code in NO_CORPORATE_INCOME_TAX:
        return 0.0, (
            f"No state corporate income tax; {NO_CORPORATE_INCOME_TAX[st_code]}"
        )
    try:
        tax_res = json.loads(fetch_state_tax_rates([st_name]))
        if isinstance(tax_res, list) and tax_res:
            item = tax_res[0] if isinstance(tax_res[0], dict) else {}
            rate = _parse_corporate_tax(item.get("Corporate Tax Rate"))
            if rate is not None:
                return rate, str(item.get("Source", "Tax Foundation"))
    except Exception as exc:
        logger.debug("Tax lookup failed for %s: %s", st_code, safe_error(exc))
    return None, "corporate tax rate unavailable"


def _electricity_rate(st_code: str) -> tuple[float | None, str]:
    try:
        elec_res = json.loads(
            fetch_state_electricity_rates([st_code], sector="industrial")
        )
        for item in elec_res if isinstance(elec_res, list) else []:
            if not isinstance(item, dict):
                continue
            if str(item.get("State", st_code)).upper() != st_code:
                continue
            # eia_skill returns "Avg Price (cents/kWh)"; "Rate" is legacy.
            raw = item.get("Avg Price (cents/kWh)", item.get("Rate"))
            value = _parse_number(raw)
            if value is not None and value > 0:
                period = item.get("Period", "latest")
                return value, f"EIA industrial average price ({period})"
    except Exception as exc:
        logger.debug(
            "Electricity lookup failed for %s: %s", st_code, safe_error(exc)
        )
    return None, "EIA electricity rate unavailable"


def _unemployment_rate(st_code: str) -> tuple[float | None, str]:
    try:
        bls_res = json.loads(analyze_labor_force_quality(st_code))
        for item in bls_res if isinstance(bls_res, list) else []:
            if isinstance(item, dict) and item.get("Status") == "Success":
                value = _parse_number(item.get("Current Value"))
                if value is not None:
                    return value, (
                        "BLS LAUS state unemployment rate "
                        f"{item.get('Current Value')}"
                    )
    except Exception as exc:
        logger.debug("BLS lookup failed for %s: %s", st_code, safe_error(exc))
    return None, "BLS unemployment rate unavailable"


def _fill_missing(
    state_data: dict[str, dict[str, Any]], criterion: str
) -> None:
    """Imputes missing values with the candidates' mean, labelled."""
    known = [
        d[criterion] for d in state_data.values() if d[criterion] is not None
    ]
    if known:
        fill = sum(known) / len(known)
        label = "imputed: average of candidates with data (source unavailable)"
    else:
        fill = _LAST_RESORT_DEFAULTS[criterion]
        label = "default assumption (source unavailable for all states)"
    for data in state_data.values():
        if data[criterion] is None:
            data[criterion] = fill
            data["basis"][criterion] += f"; {label}"
            data["fallbacks"].append(criterion)


def _min_max(value: float, low: float, high: float, invert: bool) -> float:
    if high == low:
        return 100.0
    score = (value - low) / (high - low) * 100.0
    return 100.0 - score if invert else score


def generate_location_scorecard(
    states: list[str],
    weights: dict[str, float] | None = None,
    employer_perspective: bool = True,
) -> str:
    """
    Generates a multi-variable site-selection scorecard comparing candidates states.

    Args:
        states: List of 2-letter state codes (e.g. ["TX", "NC", "OH"]).
        weights: Dictionary mapping criteria to weights (must sum to 1.0 or will be normalized).
                 Supported criteria: "corporate_tax", "electricity_rate", "labor_quality_index".
                 "labor_quality_index" is a labor-availability proxy derived from the
                 BLS LAUS statewide unemployment rate (not a skills measure).
        employer_perspective: If True, lower wages/costs score higher. If False, higher wages score higher.
                 For the labor criterion: True (employer view) scores more labor-market slack
                 (higher unemployment) higher; False (worker view) scores lower unemployment higher.

    Returns:
        JSON string containing ranked scorecard and normalized criterion scores.
    """
    try:
        # Normalize weights
        default_weights = {
            "corporate_tax": 0.35,
            "electricity_rate": 0.35,
            "labor_quality_index": 0.30,
        }

        if weights:
            # Clean and normalize user weights. Every criterion needs a
            # weight, so omitted criteria count as 0 (not missing).
            cleaned_weights = dict.fromkeys(default_weights, 0.0)
            total_w = 0.0
            for k, v in weights.items():
                k_clean = k.strip().lower()
                if k_clean in default_weights:
                    cleaned_weights[k_clean] = max(float(v), 0.0)
                    total_w += cleaned_weights[k_clean]
            if total_w > 0:
                weights = {k: v / total_w for k, v in cleaned_weights.items()}
            else:
                weights = default_weights
        else:
            weights = default_weights

        # State name mapper
        state_names = {
            "AL": "Alabama",
            "AK": "Alaska",
            "AZ": "Arizona",
            "AR": "Arkansas",
            "CA": "California",
            "CO": "Colorado",
            "CT": "Connecticut",
            "DE": "Delaware",
            "FL": "Florida",
            "GA": "Georgia",
            "HI": "Hawaii",
            "ID": "Idaho",
            "IL": "Illinois",
            "IN": "Indiana",
            "IA": "Iowa",
            "KS": "Kansas",
            "KY": "Kentucky",
            "LA": "Louisiana",
            "ME": "Maine",
            "MD": "Maryland",
            "MA": "Massachusetts",
            "MI": "Michigan",
            "MN": "Minnesota",
            "MS": "Mississippi",
            "MO": "Missouri",
            "MT": "Montana",
            "NE": "Nebraska",
            "NV": "Nevada",
            "NH": "New Hampshire",
            "NJ": "New Jersey",
            "NM": "New Mexico",
            "NY": "New York",
            "NC": "North Carolina",
            "ND": "North Dakota",
            "OH": "Ohio",
            "OK": "Oklahoma",
            "OR": "Oregon",
            "PA": "Pennsylvania",
            "RI": "Rhode Island",
            "SC": "South Carolina",
            "SD": "South Dakota",
            "TN": "Tennessee",
            "TX": "Texas",
            "UT": "Utah",
            "VT": "Vermont",
            "VA": "Virginia",
            "WA": "Washington",
            "WV": "West Virginia",
            "WI": "Wisconsin",
            "WY": "Wyoming",
        }

        # Gather data for each state
        state_data: dict[str, dict[str, Any]] = {}
        for state in states:
            st_upper = state.strip().upper()
            st_name = state_names.get(st_upper, st_upper)

            # 1. Tax Rate (lower is better)
            tax_raw, tax_basis = _tax_rate(st_upper, st_name)
            # 2. Electricity Rate (lower is better)
            elec_raw, elec_basis = _electricity_rate(st_upper)
            # 3. Labor availability (BLS LAUS unemployment rate); direction
            # depends on employer_perspective.
            labor_raw, labor_basis = _unemployment_rate(st_upper)

            state_data[st_upper] = {
                "name": st_name,
                "corporate_tax": tax_raw,
                "electricity_rate": elec_raw,
                "labor_quality_index": labor_raw,
                "basis": {
                    "corporate_tax": tax_basis,
                    "electricity_rate": elec_basis,
                    "labor_quality_index": labor_basis,
                },
                "fallbacks": [],
            }

        if not state_data:
            return json.dumps({"ERROR": "No states provided."}, indent=2)

        for criterion in default_weights:
            _fill_missing(state_data, criterion)

        # Calculate relative utility scores (0 to 100, where higher is better)
        bounds = {
            c: (
                min(d[c] for d in state_data.values()),
                max(d[c] for d in state_data.values()),
            )
            for c in default_weights
        }

        ranked_results: list[dict[str, Any]] = []
        for st_code, data in state_data.items():
            # Corporate tax / electricity: Min-Max inverted (lower is better)
            tax_score = _min_max(
                data["corporate_tax"], *bounds["corporate_tax"], invert=True
            )
            elec_score = _min_max(
                data["electricity_rate"],
                *bounds["electricity_rate"],
                invert=True,
            )
            # Labor: employer view prefers slack (higher unemployment).
            labor_score = _min_max(
                data["labor_quality_index"],
                *bounds["labor_quality_index"],
                invert=not employer_perspective,
            )

            # Composite weighted score
            composite = (
                tax_score * weights["corporate_tax"]
                + elec_score * weights["electricity_rate"]
                + labor_score * weights["labor_quality_index"]
            )

            def _flag(criterion: str, _data: dict = data) -> str:
                return " [FALLBACK]" if criterion in _data["fallbacks"] else ""

            ranked_results.append(
                {
                    "State_Code": st_code,
                    "State_Name": data["name"],
                    "Composite_Score": round(composite, 1),
                    "Criteria_Scores": {
                        "Corporate_Tax": f"{tax_score:.1f}/100 (Tax Rate: {data['corporate_tax']:.2f}%){_flag('corporate_tax')}",
                        "Electricity_Rate": f"{elec_score:.1f}/100 (Power: {data['electricity_rate']:.2f}¢/kWh){_flag('electricity_rate')}",
                        "Labor_Quality": f"{labor_score:.1f}/100 (Unemployment: {data['labor_quality_index']:.2f}%){_flag('labor_quality_index')}",
                    },
                    "Data_Basis": {
                        "Corporate_Tax": data["basis"]["corporate_tax"],
                        "Electricity_Rate": data["basis"]["electricity_rate"],
                        "Labor_Quality": data["basis"]["labor_quality_index"],
                    },
                    "Fallbacks_Used": data["fallbacks"],
                }
            )

        # Sort by Composite Score descending
        ranked_results.sort(key=lambda x: x["Composite_Score"], reverse=True)

        # Build rank field
        for idx, item in enumerate(ranked_results):
            item["Rank"] = idx + 1

        return json.dumps(
            {
                "Scorecard_Summary": ranked_results,
                "Criteria_Weights": {
                    k: f"{v * 100:.1f}%" for k, v in weights.items()
                },
                "Interpretation": "Composite scores range from 0 to 100. Higher composite score indicates a better matched location based on your weights.",
                "Methodology": (
                    "Scores are min-max normalized across the candidate "
                    "states. Corporate tax: top marginal state corporate "
                    "income tax rate (0% where there is none; gross receipts "
                    "taxes are not modelled). Electricity: EIA industrial "
                    "average retail price. Labor: labor-availability proxy "
                    "from the BLS LAUS statewide unemployment rate ("
                    + (
                        "employer view: more slack scores higher"
                        if employer_perspective
                        else "worker view: lower unemployment scores higher"
                    )
                    + "). Criteria marked [FALLBACK] had no live data and "
                    "were imputed; see Data_Basis."
                ),
                "Source": "Site Selection Decision Engine (Tax Foundation, EIA, BLS LAUS)",
            },
            indent=2,
        )

    except Exception as e:
        return json.dumps(
            {"ERROR": f"Scorecard generation failed: {safe_error(e)}"},
            indent=2,
        )
