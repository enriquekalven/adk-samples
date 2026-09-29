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

"""MLS Property Analysis and Real Estate Investment Yield Calculator Skill with RentCast API integration."""

import json
import logging
from typing import Any

import requests

from economic_research.shared_libraries.helper import (
    HTTP_TIMEOUT_SECONDS,
    SANDBOX_SOURCE,
    get_session_api_key,
    safe_error,
)
from economic_research.tools.hud_skill import (
    fetch_hud_fmr_data,
    fetch_hud_usps_crosswalk,
)

logger = logging.getLogger(__name__)

RENTCAST_SOURCE = "RentCast Listings API (live)"
# Assumed 2BR monthly rent when HUD FMR cannot be retrieved (labelled in
# the output as a default, never as HUD data).
DEFAULT_FMR_2BR = 1500.0

# Grounded city-to-county FIPS mappings for HUD integration (fallback)
CITY_FIPS_MAP = {
    "austin": "48453",  # Travis County, TX
    "raleigh": "37183",  # Wake County, NC
    "dallas": "48113",  # Dallas County, TX
    "columbus": "39049",  # Franklin County, OH
}

PROPERTY_TYPE_MAP = {
    "multifamily": "Multi-Family",
    "multi-family": "Multi-Family",
    "single-family": "Single Family",
    "singlefamily": "Single Family",
    "condo": "Condo",
    "townhouse": "Townhouse",
    "land": "Land",
    "commercial": "Commercial",
}

CITY_STATE_MAP = {
    "austin": "TX",
    "raleigh": "NC",
    "dallas": "TX",
    "columbus": "OH",
}


def fetch_mls_property_listings(
    city_name: str,
    max_price: float | None = None,
    property_type: str = "multifamily",
) -> str:
    """
    Queries MLS listings for a target metropolitan area (either live via RentCast or from
    the sandbox database fallback) and performs automated investment analysis (Cap Rate,
    Price-to-Rent Ratio) by correlating listing prices with local HUD Fair Market Rent (FMR) benchmarks.

    Args:
        city_name: Name of the target city (e.g., "Austin", "Raleigh", "Columbus", "Dallas").
        max_price: Optional maximum listing price filter in USD.
        property_type: Type of property: "multifamily", "single-family", or "condo".

    Returns:
        JSON string containing active listings, estimated local rents, annual expenses, and Cap Rates.
        Each listing carries a "Source" field; sandbox listings are labelled as illustrative, not live.
    """
    city_clean = city_name.lower().strip().split(",")[0]
    api_key = (get_session_api_key("RENTCAST_API_KEY") or "").strip()

    raw_listings: list[dict[str, Any]] = []

    # 1. Try fetching from live RentCast API if API key is set
    if api_key:
        url = "https://api.rentcast.io/v1/listings/sale"

        parts = city_name.split(",")
        city = parts[0].strip()
        state = (
            parts[1].strip().upper()
            if len(parts) > 1
            else CITY_STATE_MAP.get(city.lower())
        )

        mapped_type = PROPERTY_TYPE_MAP.get(
            property_type.lower().strip(), "Multi-Family"
        )

        params: dict[str, Any] = {
            "city": city,
            "propertyType": mapped_type,
            "status": "Active",
            "limit": 3,  # Conserve user's 50 requests/month free quota limit
        }
        if state:
            params["state"] = state

        try:
            headers = {"accept": "application/json", "X-Api-Key": api_key}
            resp = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=HTTP_TIMEOUT_SECONDS,
            )
            if resp.status_code == 200:
                data = resp.json()
                for item in data if isinstance(data, list) else []:
                    raw_listings.append(
                        {
                            "address": item.get("formattedAddress"),
                            "price": item.get("price"),
                            "beds": item.get("bedrooms", 2),
                            "baths": item.get("bathrooms", 1.5),
                            "type": property_type.lower(),
                            "zip": item.get("zipCode"),
                            "source": RENTCAST_SOURCE,
                        }
                    )
            else:
                # Never log the response body: it can echo request details.
                logger.warning(
                    "RentCast API returned HTTP %s; falling back to sandbox "
                    "listings.",
                    resp.status_code,
                )
        except Exception as e:
            logger.warning(
                "RentCast request failed (%s); falling back to sandbox "
                "listings.",
                safe_error(e),
            )

    # 2. Fall back to mock active listings if no key was present or no listings were fetched
    if not raw_listings:
        listings_db: dict[str, list[dict[str, Any]]] = {
            "austin": [
                {
                    "address": "1208 Chicon St, Austin, TX 78702",
                    "price": 450000,
                    "beds": 2,
                    "baths": 1.5,
                    "type": "condo",
                },
                {
                    "address": "7402 Decker Ln, Austin, TX 78724",
                    "price": 380000,
                    "beds": 3,
                    "baths": 2,
                    "type": "single-family",
                },
                {
                    "address": "1611 E 2nd St, Austin, TX 78702",
                    "price": 650000,
                    "beds": 2,
                    "baths": 2,
                    "type": "multifamily",
                },
            ],
            "raleigh": [
                {
                    "address": "412 E South St, Raleigh, NC 27601",
                    "price": 310000,
                    "beds": 2,
                    "baths": 1,
                    "type": "condo",
                },
                {
                    "address": "2910 Avent Ferry Rd, Raleigh, NC 27606",
                    "price": 395000,
                    "beds": 3,
                    "baths": 2.5,
                    "type": "single-family",
                },
                {
                    "address": "905 S Saunders St, Raleigh, NC 27603",
                    "price": 480000,
                    "beds": 4,
                    "baths": 3,
                    "type": "multifamily",
                },
            ],
            "columbus": [
                {
                    "address": "84 Indianola Ave, Columbus, OH 43201",
                    "price": 280000,
                    "beds": 2,
                    "baths": 1.5,
                    "type": "condo",
                },
                {
                    "address": "1042 S High St, Columbus, OH 43206",
                    "price": 340000,
                    "beds": 3,
                    "baths": 2,
                    "type": "single-family",
                },
                {
                    "address": "512 E Maynard Ave, Columbus, OH 43202",
                    "price": 390000,
                    "beds": 4,
                    "baths": 2,
                    "type": "multifamily",
                },
            ],
            "dallas": [
                {
                    "address": "2903 Fitzhugh Ave, Dallas, TX 75204",
                    "price": 330000,
                    "beds": 2,
                    "baths": 2,
                    "type": "condo",
                },
                {
                    "address": "4120 Simpson St, Dallas, TX 75246",
                    "price": 390000,
                    "beds": 3,
                    "baths": 2,
                    "type": "single-family",
                },
                {
                    "address": "5208 Columbia Ave, Dallas, TX 75214",
                    "price": 550000,
                    "beds": 4,
                    "baths": 3,
                    "type": "multifamily",
                },
            ],
        }

        mock_raw = listings_db.get(city_clean, [])
        for item in mock_raw:
            # Extract ZIP code from end of address string
            try:
                zip_code = item["address"].split(",")[-1].strip().split(" ")[-1]
            except Exception:
                zip_code = None

            raw_listings.append(
                {
                    "address": item["address"],
                    "price": item["price"],
                    "beds": item["beds"],
                    "baths": item["baths"],
                    "type": item["type"],
                    "zip": zip_code,
                    "source": SANDBOX_SOURCE,
                }
            )

    if not raw_listings:
        return json.dumps(
            {
                "status": "No listings found",
                "city": city_name,
                "message": f"MLS integration has no active properties for '{city_name}'.",
            },
            indent=2,
        )

    # 3. Filter listings
    eligible = []
    for prop in raw_listings:
        # Live RentCast listings can omit fields or report price None/0;
        # skip them rather than crash on the cap-rate division below.
        price = prop.get("price")
        if (
            not isinstance(price, (int, float))
            or isinstance(price, bool)
            or price <= 0
        ):
            continue
        prop_type = str(prop.get("type") or "unknown")

        # Filter by price
        if max_price and price > max_price:
            continue

        # Filter by property type
        if property_type and prop_type.lower() != property_type.lower():
            continue
        eligible.append(prop)

    # 4. Get local HUD FMR data once per city (not once per listing): at
    # most one crosswalk, one resolver and one FMR call per request.
    hud_rent_2br, hud_label = (
        _city_hud_rent(city_name, eligible) if eligible else (0.0, "")
    )

    # 5. Analyze listings
    analyzed_listings = []
    for prop in eligible:
        price = prop["price"]
        prop_type = str(prop.get("type") or "unknown")

        # Adjust estimated monthly rent based on bed count (vs 2BR HUD base)
        beds_raw = prop.get("beds")
        beds = (
            beds_raw
            if isinstance(beds_raw, (int, float)) and beds_raw > 0
            else 2
        )
        bed_multiplier = 1.0
        if beds == 1:
            bed_multiplier = 0.8
        elif beds == 3:
            bed_multiplier = 1.25
        elif beds >= 4:
            bed_multiplier = 1.5

        est_monthly_rent = hud_rent_2br * bed_multiplier
        est_annual_rent = est_monthly_rent * 12

        # Operational expenses: 35% of gross rent
        est_annual_expenses = est_annual_rent * 0.35
        net_operating_income = est_annual_rent - est_annual_expenses

        # Calculate Cap Rate (%)
        cap_rate = (net_operating_income / price) * 100

        # Price-to-Rent Ratio
        price_to_rent = price / est_annual_rent if est_annual_rent else 0.0

        analyzed_listings.append(
            {
                "Address": prop.get("address", "N/A"),
                "Price": f"${price:,}",
                "Property Type": prop_type.capitalize(),
                "Beds/Baths": f"{beds}B/{prop.get('baths', 'N/A')}Ba",
                "HUD FMR (2BR)": f"${hud_rent_2br:,.0f} ({hud_label})",
                "Est. Monthly Rent": f"${est_monthly_rent:,.2f}",
                "Est. Annual Expenses": f"${est_annual_expenses:,.2f}",
                "Net Operating Income": f"${net_operating_income:,.2f}",
                "Price-to-Rent Ratio": f"{price_to_rent:.1f}x",
                "Estimated Cap Rate": f"{cap_rate:.2f}%",
                "Source": prop.get("source", SANDBOX_SOURCE),
            }
        )

    return json.dumps(analyzed_listings, indent=2)


def _city_hud_rent(
    city_name: str, listings: list[dict[str, Any]]
) -> tuple[float, str]:
    """HUD 2BR Fair Market Rent for the city and a label for its basis.

    Resolves the county FIPS once: HUD USPS crosswalk on the first listing
    ZIP, else the Dynamic Entity Resolver (which is given the state, when
    present, so it cannot map to a same-named county in another state).
    """
    fips = None
    zip_code = next((p["zip"] for p in listings if p.get("zip")), None)
    if zip_code:
        try:
            cross_resp = json.loads(fetch_hud_usps_crosswalk(zip_code))
            if isinstance(cross_resp, dict) and "County_FIPS" in cross_resp:
                fips = cross_resp["County_FIPS"]
        except Exception as exc:
            logger.debug("HUD crosswalk failed: %s", safe_error(exc))

    # If dynamic FIPS lookup fails, fall back to our evolved Dynamic Entity Resolver
    if not fips:
        from economic_research.tools.dynamic_entity_resolver import (
            resolve_fips,
        )

        fips = resolve_fips(city_name)  # '' when unresolved

    if fips:
        try:
            hud_resp = json.loads(fetch_hud_fmr_data(fips))
            if isinstance(hud_resp, dict) and "Rent_2BR" in hud_resp:
                rent = float(
                    hud_resp["Rent_2BR"].replace("$", "").replace(",", "")
                )
                return rent, str(hud_resp.get("Year", "HUD FMR"))
        except Exception as exc:
            logger.debug("HUD FMR lookup failed: %s", safe_error(exc))

    return DEFAULT_FMR_2BR, "default assumption; HUD FMR unavailable"
