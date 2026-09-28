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

"""ADK Skill: FRED Semantic Series Search and Mapping Helper."""

import json

# Top macroeconomic series definitions on FRED
MACRO_SERIES_MAP = {
    "gdp": [
        {
            "series_id": "GDPC1",
            "description": "Real Gross Domestic Product (Quarterly, Billions of Chained 2017 Dollars)",
        },
        {
            "series_id": "GDP",
            "description": "Gross Domestic Product (Quarterly, Billions of Dollars)",
        },
    ],
    "unemployment": [
        {
            "series_id": "UNRATE",
            "description": "Civilian Unemployment Rate (Monthly, Percent)",
        },
        {
            "series_id": "NROU",
            "description": "Noncyclical Rate of Unemployment (Quarterly, Percent)",
        },
    ],
    "cpi": [
        {
            "series_id": "CPIAUCSL",
            "description": "Consumer Price Index for All Urban Consumers: All Items (Monthly, Index)",
        },
        {
            "series_id": "CPILFESL",
            "description": "Consumer Price Index for All Urban Consumers: All Items Less Food and Energy (Monthly, Index)",
        },
    ],
    "inflation": [
        {
            "series_id": "CPIAUCSL",
            "description": "Consumer Price Index for All Urban Consumers: All Items (Monthly, Index)",
        },
        {
            "series_id": "CPILFESL",
            "description": "Consumer Price Index for All Urban Consumers: All Items Less Food and Energy (Monthly, Index)",
        },
    ],
    "mortgage": [
        {
            "series_id": "MORTGAGE30US",
            "description": "30-Year Fixed Rate Mortgage Average in the United States (Weekly, Percent)",
        },
        {
            "series_id": "MORTGAGE15US",
            "description": "15-Year Fixed Rate Mortgage Average in the United States (Weekly, Percent)",
        },
    ],
    "fed_funds": [
        {
            "series_id": "FEDFUNDS",
            "description": "Effective Federal Funds Rate (Monthly, Percent)",
        }
    ],
    "treasury": [
        {
            "series_id": "DGS10",
            "description": "Market Yield on U.S. Treasury Securities at 10-Year Constant Maturity (Daily, Percent)",
        },
        {
            "series_id": "DGS2",
            "description": "Market Yield on U.S. Treasury Securities at 2-Year Constant Maturity (Daily, Percent)",
        },
    ],
    "household_income": [
        {
            "series_id": "MEHOINUSA672N",
            "description": "Real Median Household Income in the United States (Annual, Adjusted Dollars)",
        }
    ],
}


def search_macro_series(query: str) -> str:
    """
    Helper tool mapping semantic keyword queries to valid FRED Series IDs.

    Args:
        query: The topic or term to lookup (e.g. "gdp", "unemployment", "mortgage", "inflation").

    Returns:
        JSON string containing list of valid FRED Series IDs and descriptions.
    """
    clean_q = query.strip().lower().replace(" ", "_")

    # Exact or substring match in mapping keys
    matches = []
    for key, series_list in MACRO_SERIES_MAP.items():
        if clean_q in key or key in clean_q:
            matches.extend(series_list)

    if not matches:
        # Return fallback with instructions
        all_topics = list(MACRO_SERIES_MAP.keys())
        return json.dumps(
            {
                "Warning": f"No direct match found for query '{query}'.",
                "Suggestions": [
                    {
                        "topic": t,
                        "series_ids": [
                            s["series_id"] for s in MACRO_SERIES_MAP[t]
                        ],
                    }
                    for t in all_topics
                ],
                "Source": "FRED Semantic Search Helper",
            },
            indent=2,
        )

    return json.dumps(
        {
            "Query": query,
            "Matches": matches,
            "Source": "FRED Semantic Search Helper",
        },
        indent=2,
    )
