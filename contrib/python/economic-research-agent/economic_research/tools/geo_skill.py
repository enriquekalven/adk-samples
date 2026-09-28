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

"""ADK Skill: Unified Geo-Search. Maps names to FIPS/MSA codes."""

import json

from us import states

# High-fidelity FIPS mapping for common site-selection hubs
COUNTY_FIPS_REGISTRY = {
    "Texas": {
        "Travis": "48453",
        "Dallas": "48113",
        "Harris": "48201",
        "Bexar": "48029",
        "Tarrant": "48439",
        "Austin": "48453",  # Mapping City to primary County
    },
    "North Carolina": {
        "Wake": "37183",
        "Durham": "37063",
        "Mecklenburg": "37119",
        "Raleigh": "37183",
    },
    "Tennessee": {"Davidson": "47037", "Shelby": "47157", "Nashville": "47037"},
    "Colorado": {"Denver": "08031"},
    "Washington": {"King": "53033", "Seattle": "53033"},
    "California": {"San Francisco": "06075", "Santa Clara": "06085"},
}


def get_region_identifiers(
    state_abbr: str, county_name: str | None = None
) -> str:
    """
    Standardizes regional identifiers (FIPS codes) for use in other economic skills.
    Translates 'Travis County' or 'Austin' into '48453'.
    """
    try:
        state_obj = states.lookup(state_abbr)
        if not state_obj:
            return json.dumps(
                {"ERROR": f"Invalid state abbreviation: {state_abbr}"}, indent=2
            )

        result = {
            "State Name": state_obj.name,
            "State Abbr": state_obj.abbr,
            "State FIPS": state_obj.fips,
        }

        if county_name:
            # Look up in our hardened registry
            lookup_key = county_name.replace(" County", "").strip()
            county_fips = COUNTY_FIPS_REGISTRY.get(state_obj.name, {}).get(
                lookup_key
            )

            result["County"] = lookup_key
            result["County FIPS"] = (
                county_fips or f"UNKNOWN (Search Census for {lookup_key})"
            )

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({"ERROR": str(e)}, indent=2)
