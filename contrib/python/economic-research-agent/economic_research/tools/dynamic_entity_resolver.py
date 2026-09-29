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

"""ADK Tool: Dynamic Entity and Geography Resolver (FIPS, MSA, and HS Codes).
Evolved autonomously by AlphaEvolve using live Serper.dev integration to provide infinite geographic coverage.

Resolution never guesses: when a place cannot be resolved (or the resolved
code contradicts the state given in the input, e.g. "Orange County, CA"
matching Orange County, FL), ``resolve_fips`` / ``resolve_msa_code`` return
``UNRESOLVED`` (an empty string, so ``if fips:`` checks in callers skip the
lookup) and ``resolve_fips_details`` / ``resolve_msa_details`` explain why.
"""

import json
import logging
import os
import re
import urllib.request
from typing import Any

from economic_research.shared_libraries.helper import (
    get_session_api_key,
    safe_error,
)

logger = logging.getLogger(__name__)

# Returned by resolve_fips / resolve_msa_code when a place cannot be
# resolved. Falsy on purpose so callers can use ``if fips:``.
UNRESOLVED = ""

# USPS abbreviation -> 2-digit state FIPS code (50 states, DC, PR).
STATE_FIPS = {
    "AL": "01",
    "AK": "02",
    "AZ": "04",
    "AR": "05",
    "CA": "06",
    "CO": "08",
    "CT": "09",
    "DE": "10",
    "DC": "11",
    "FL": "12",
    "GA": "13",
    "HI": "15",
    "ID": "16",
    "IL": "17",
    "IN": "18",
    "IA": "19",
    "KS": "20",
    "KY": "21",
    "LA": "22",
    "ME": "23",
    "MD": "24",
    "MA": "25",
    "MI": "26",
    "MN": "27",
    "MS": "28",
    "MO": "29",
    "MT": "30",
    "NE": "31",
    "NV": "32",
    "NH": "33",
    "NJ": "34",
    "NM": "35",
    "NY": "36",
    "NC": "37",
    "ND": "38",
    "OH": "39",
    "OK": "40",
    "OR": "41",
    "PA": "42",
    "RI": "44",
    "SC": "45",
    "SD": "46",
    "TN": "47",
    "TX": "48",
    "UT": "49",
    "VT": "50",
    "VA": "51",
    "WA": "53",
    "WV": "54",
    "WI": "55",
    "WY": "56",
    "PR": "72",
}

# USPS abbreviation -> full state name.
STATE_NAMES = {
    "AL": "Alabama",
    "AK": "Alaska",
    "AZ": "Arizona",
    "AR": "Arkansas",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "DC": "District of Columbia",
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
    "PR": "Puerto Rico",
}
_STATE_NAME_TO_ABBR = {name.lower(): abbr for abbr, name in STATE_NAMES.items()}
_VALID_STATE_FIPS = frozenset(STATE_FIPS.values())

# Curated entity cache for fast, direct resolution. Static and hand-checked:
# results discovered via Serper are NOT written back here, so one bad search
# result cannot poison every later session in the process.
ENTITY_CACHE = {
    "fips": {
        "austin": "48453",
        "travis": "48453",
        "scranton": "42069",
        "lackawanna": "42069",
        "orlando": "12095",
        "orange": "12095",
        "miami": "12086",
        "miami-dade": "12086",
        "pittsburgh": "42003",
        "allegheny": "42003",
        "philadelphia": "42101",
        "tampa": "12057",
        "hillsborough": "12057",
        "houston": "48201",
        "harris": "48201",
        "dallas": "48113",
        "seattle": "53033",
        "king": "53033",
        "boise": "16001",
        "ada": "16001",
        "columbus": "39049",
        "franklin": "39049",
        "raleigh": "37183",
        "wake": "37183",
    },
    "msa": {
        "austin": "12420",
        "nashville": "34980",
        "raleigh": "39580",
        "columbus": "18140",
        "dallas": "19100",
        "denver": "19740",
        "seattle": "42660",
        "boise": "14260",
    },
}

# State of each curated MSA (county FIPS carry their state in the prefix).
_MSA_STATES = {
    "12420": "TX",
    "34980": "TN",
    "39580": "NC",
    "18140": "OH",
    "19100": "TX",
    "19740": "CO",
    "42660": "WA",
    "14260": "ID",
}

# Words that do not identify a place ("Greater Austin Metro Area").
_FILLER_TOKENS = frozenset(
    {
        "county",
        "parish",
        "borough",
        "city",
        "of",
        "the",
        "greater",
        "metro",
        "metropolitan",
        "area",
        "msa",
        "region",
    }
)


def _parse_state(text: str) -> str | None:
    """Returns the USPS abbreviation named by ``text`` (e.g. 'TX 78701')."""
    cleaned = re.sub(r"[^a-z ]", " ", text.lower())
    cleaned = " ".join(cleaned.split())
    if not cleaned:
        return None
    if cleaned in _STATE_NAME_TO_ABBR:
        return _STATE_NAME_TO_ABBR[cleaned]
    first = cleaned.split()[0].upper()
    if first in STATE_FIPS:
        return first
    for name, abbr in _STATE_NAME_TO_ABBR.items():
        if cleaned.startswith(name + " "):
            return abbr
    return None


def _split_place(value: str) -> tuple[list[str], str | None]:
    """Splits 'Orange County, CA' into (candidate keys, state abbr)."""
    parts = [p.strip() for p in value.split(",")]
    name = parts[0].lower()
    state = None
    for part in parts[1:]:
        state = _parse_state(part)
        if state:
            break

    def _key(text: str) -> str:
        tokens = re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", text)
        return " ".join(t for t in tokens if t not in _FILLER_TOKENS)

    # Whole-token keys only (no substring matching): "miami-dade county"
    # -> "miami-dade", "miami dade", "miami"; "west orange" stays as-is.
    candidates: list[str] = []
    for text in (name, name.replace("-", " "), name.split("-")[0]):
        key = _key(text)
        if key and key not in candidates:
            candidates.append(key)
    return candidates, state


def _unresolved(value: Any, reason: str) -> dict[str, Any]:
    logger.warning("Could not resolve %r: %s", value, reason)
    return {
        "input": value,
        "code": UNRESOLVED,
        "status": "unresolved",
        "method": None,
        "reason": reason,
    }


def _serper_text(query: str) -> str | None:
    """Returns concatenated Serper organic/answerBox text, or None."""
    api_key = (
        get_session_api_key("SERPER_API_KEY", os.getenv("SERPER_API_KEY")) or ""
    ).strip()
    if not api_key:
        return None
    req = urllib.request.Request(
        "https://google.serper.dev/search",
        data=json.dumps({"q": query}).encode("utf-8"),
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=8) as response:  # noqa: S310
        res = json.loads(response.read().decode("utf-8"))
    return str(res.get("organic", "")) + str(res.get("answerBox", ""))


def _pick_fips(text: str, state: str | None) -> str | None:
    """Picks a county FIPS from search text, validating the state prefix.

    Only 5-digit numbers that follow the word 'FIPS' are considered (so ZIP
    codes and years are not picked up blindly), and the 2-digit state prefix
    must be a real state code that matches ``state`` when one is given.
    """
    state_fips = STATE_FIPS.get(state) if state else None
    for match in re.finditer(r"(?i)fips\D{0,40}?(\d{5})\b", text):
        code = match.group(1)
        if code[:2] not in _VALID_STATE_FIPS or code.endswith("000"):
            continue
        if state_fips and code[:2] != state_fips:
            continue
        return code
    return None


def _pick_msa(text: str) -> str | None:
    """Picks a CBSA code from search text.

    CBSA codes are 5 digits in 10000-49999 ending in 0; only numbers next to
    'CBSA'/'MSA' are considered.
    """
    pattern = r"(?i)\b(?:cbsa|msa)\D{0,40}?(\d{5})\b"
    for match in re.finditer(pattern, text):
        code = match.group(1)
        if 10000 <= int(code) <= 49999 and code.endswith("0"):
            return code
    return None


def resolve_fips_details(value: Any) -> dict[str, Any]:
    """Resolves a county FIPS code and explains how (or why not).

    Returns a dict with ``code`` (5-digit FIPS, 2-digit state FIPS, or
    ``UNRESOLVED``), ``status`` ('resolved'/'unresolved'), ``method``
    ('input', 'cache', 'serper') and ``reason`` when unresolved.
    """
    if isinstance(value, list):
        value = value[0] if value else None
    if not value or not str(value).strip():
        return _unresolved(value, "No location provided.")

    val_str = str(value).strip()
    if val_str.isdigit():
        if len(val_str) in (2, 5) and val_str[:2] in _VALID_STATE_FIPS:
            return {
                "input": value,
                "code": val_str,
                "status": "resolved",
                "method": "input",
            }
        return _unresolved(value, f"'{val_str}' is not a valid FIPS code.")

    candidates, state = _split_place(val_str)
    state_fips = STATE_FIPS.get(state) if state else None

    for key in candidates:
        code = ENTITY_CACHE["fips"].get(key)
        if not code:
            continue
        if state_fips and code[:2] != state_fips:
            # e.g. "Orange County, CA" must not map to Orange County, FL.
            logger.info(
                "Cache hit %s for %r rejected: not in %s", code, key, state
            )
            continue
        return {
            "input": value,
            "code": code,
            "status": "resolved",
            "method": "cache",
        }

    # Dynamic live discovery fallback via Serper (validated, never cached).
    name = candidates[0] if candidates else val_str.lower()
    state_label = STATE_NAMES.get(state, "") if state else ""
    try:
        text = _serper_text(f"{name} county {state_label} FIPS code".strip())
        if text:
            code = _pick_fips(text, state)
            if code:
                logger.info("Discovered FIPS via Serper for %r: %s", name, code)
                return {
                    "input": value,
                    "code": code,
                    "status": "resolved",
                    "method": "serper",
                }
    except Exception as e:
        logger.warning(
            "Serper FIPS discovery failed for %r: %s", name, safe_error(e)
        )

    return _unresolved(
        value,
        "No curated or validated FIPS match"
        + (f" in {state}." if state else ".")
        + " Provide a 5-digit county FIPS code.",
    )


def resolve_fips(value: Any) -> str:
    """
    Robustly extracts, maps, and dynamically discovers county FIPS codes using Serper.dev API if missing from cache.

    Returns ``UNRESOLVED`` ('') when the place cannot be resolved; it never
    silently substitutes another county.
    """
    return resolve_fips_details(value)["code"]


def resolve_msa_details(value: Any) -> dict[str, Any]:
    """Resolves a CBSA/MSA code and explains how (or why not)."""
    if isinstance(value, list):
        value = value[0] if value else None
    if not value or not str(value).strip():
        return _unresolved(value, "No location provided.")

    val_str = str(value).strip()
    if val_str.isdigit():
        if len(val_str) == 5:
            return {
                "input": value,
                "code": val_str,
                "status": "resolved",
                "method": "input",
            }
        return _unresolved(value, f"'{val_str}' is not a valid MSA code.")

    candidates, state = _split_place(val_str)
    for key in candidates:
        code = ENTITY_CACHE["msa"].get(key)
        if not code:
            continue
        if state and _MSA_STATES.get(code) not in (None, state):
            logger.info(
                "Cache hit %s for %r rejected: not in %s", code, key, state
            )
            continue
        return {
            "input": value,
            "code": code,
            "status": "resolved",
            "method": "cache",
        }

    # Dynamic Live Discovery via Serper (validated, never cached)
    name = candidates[0] if candidates else val_str.lower()
    state_label = STATE_NAMES.get(state, "") if state else ""
    try:
        text = _serper_text(f"{name} {state_label} MSA CBSA code".strip())
        if text:
            code = _pick_msa(text)
            if code:
                logger.info("Discovered MSA via Serper for %r: %s", name, code)
                return {
                    "input": value,
                    "code": code,
                    "status": "resolved",
                    "method": "serper",
                }
    except Exception as e:
        logger.warning(
            "Serper MSA discovery failed for %r: %s", name, safe_error(e)
        )

    return _unresolved(value, "No curated or validated MSA/CBSA match.")


def resolve_msa_code(value: Any) -> str:
    """
    Resolves the Federal Reserve / FRED MSA code for a given city or metro name.

    Returns ``UNRESOLVED`` ('') when the metro cannot be resolved.
    """
    return resolve_msa_details(value)["code"]
