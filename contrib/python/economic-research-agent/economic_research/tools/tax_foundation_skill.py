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

"""ADK Skill: Tax Foundation Scraper. Real-time state corporate tax data."""

import json
import logging
import re

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

from economic_research.shared_libraries.helper import (
    HTTP_TIMEOUT_SECONDS,
    SANDBOX_SOURCE,
    safe_error,
)
from economic_research.tools.dynamic_entity_resolver import STATE_NAMES

logger = logging.getLogger(__name__)

TAX_FOUNDATION_URL = "https://taxfoundation.org/data/all/state/state-corporate-income-tax-rates-brackets-2024/"
# Tax year of the scraped table, surfaced in every result.
_URL_YEAR = re.search(r"(20\d{2})/?$", TAX_FOUNDATION_URL)
TAX_YEAR = _URL_YEAR.group(1) if _URL_YEAR else "unknown"

_NAME_TO_CANONICAL = {name.lower(): name for name in STATE_NAMES.values()}

# Hardcoded fallback (illustrative; labelled SANDBOX_SOURCE). States with no
# corporate income tax say "None"; TX/OH/WA/NV levy gross receipts taxes.
FALLBACK_RATES = {
    "Texas": "None (Gross Receipts Tax)",
    "California": "8.84%",
    "New York": "7.25%",
    "Florida": "5.5%",
    "Illinois": "9.5%",
    "Pennsylvania": "8.49%",
    "Ohio": "None (Gross Receipts Tax)",
    "Washington": "None (Gross Receipts Tax)",
    "Nevada": "None (Gross Receipts Tax)",
    "South Dakota": "None",
    "Wyoming": "None",
    "North Carolina": "2.5%",
    "Arizona": "4.9%",
}


class TaxRequest(BaseModel):
    state_names: list[str] = Field(
        ...,
        description="List of full state names (e.g., ['Texas', 'California']).",
    )


def _canonical_state(state: str) -> str | None:
    """'texas', 'Texas' or 'TX' -> 'Texas' (None if not a state)."""
    cleaned = " ".join(state.split()).strip()
    if cleaned.upper() in STATE_NAMES:
        return STATE_NAMES[cleaned.upper()]
    return _NAME_TO_CANONICAL.get(cleaned.lower())


def _scrape_rates(html: str) -> dict[str, str]:
    """Parses {state name: rate text} from the Tax Foundation table.

    Multi-bracket states span several rows with an empty state cell; their
    rates are joined ("1% / 2% / ...") so the top marginal rate is kept.
    """
    soup = BeautifulSoup(html, "html.parser")
    tax_data: dict[str, list[str]] = {}
    for table in soup.find_all("table"):
        current = None
        for row in table.find_all("tr"):
            cols = row.find_all(["td", "th"])
            if len(cols) < 2:
                continue
            # Clean up footnote references like 'Alaska (a)'
            state_raw = cols[0].get_text(" ", strip=True).split("(")[0]
            rate_raw = cols[1].get_text(" ", strip=True)
            state = _canonical_state(state_raw) if state_raw.strip() else None
            if state:
                current = state
                tax_data.setdefault(state, [])
            elif state_raw.strip():
                current = None  # header/other row
                continue
            if current and rate_raw:
                tax_data[current].append(rate_raw)
    return {s: " / ".join(r) for s, r in tax_data.items() if r}


def fetch_state_tax_rates(state_names: list[str]) -> str:
    """
    Scrapes Tax Foundation for the latest state corporate income tax rates.
    This bypasses legacy BigQuery dependencies and provides real-time data.

    Accepts full state names or 2-letter codes (case-insensitive). Each
    result includes the tax year of the source table.
    """
    try:
        response = requests.get(
            TAX_FOUNDATION_URL, timeout=HTTP_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        tax_data = _scrape_rates(response.text)

        requested = [_canonical_state(s) for s in state_names]
        if not any(tax_data.get(s) for s in requested if s):
            # Every requested state is missing: the page layout most
            # likely changed. Do not return a silent N/A for everyone.
            raise ValueError(
                "Tax Foundation page structure changed; no state rates "
                "could be parsed"
            )

        results = []
        for state, canonical in zip(state_names, requested, strict=True):
            rate = tax_data.get(canonical) if canonical else None
            item = {
                "State": state,
                "Corporate Tax Rate": rate or "N/A (Check Source)",
                "Tax Year": TAX_YEAR,
                "Source": f"Tax Foundation (Live Scrape {TAX_YEAR})",
            }
            if not canonical:
                item["Warning"] = f"'{state}' is not a recognized US state."
            elif not rate:
                item["Warning"] = "State not found in the scraped table."
            results.append(item)

        return json.dumps(results, indent=2)

    except Exception as e:
        # Fallback to a known list if scraping fails (Hardening)
        error = safe_error(e)
        logger.warning("Tax Foundation scrape failed: %s", error)
        results = []
        for state in state_names:
            canonical = _canonical_state(state)
            results.append(
                {
                    "State": state,
                    "Corporate Tax Rate": FALLBACK_RATES.get(
                        canonical or "", "N/A"
                    ),
                    "Tax Year": TAX_YEAR,
                    "Source": f"{SANDBOX_SOURCE} - hardcoded Tax Foundation "
                    f"{TAX_YEAR} rates",
                    "Error": error
                    if "404" not in error
                    else "Page structure changed",
                }
            )
        return json.dumps(results, indent=2)


if __name__ == "__main__":
    # Test
    print(fetch_state_tax_rates(["Texas", "California", "Minnesota"]))
