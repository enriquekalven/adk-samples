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

"""ADK Skill: Census ACS. Demographic & Educational Attainment."""

import json
import os

import requests

from economic_research.shared_libraries.helper import get_session_api_key


def fetch_census_education_stats(city_names: list[str]) -> str:
    """
    Fetches real educational attainment statistics from the Census ACS API.
    Essential for talent-pipeline assessments in site selection.
    """
    c_key = (
        get_session_api_key("CENSUS_API_KEY", os.getenv("CENSUS_API_KEY")) or ""
    ).strip()
    census_key = c_key.replace('"', "").replace("'", "")
    if not census_key:
        return json.dumps(
            {"ERROR": "CENSUS_API_KEY not found in environment."}, indent=2
        )

    # Simplified Census County Mapping for Grounded Reliability
    # Format: [State FIPS][County FIPS]
    city_to_fips = {
        "austin": "48453",
        "raleigh": "37183",
        "seattle": "53033",
        "nashville": "47037",
        "denver": "08031",
    }

    try:
        results = []
        for city in city_names:
            city_clean = city.lower().split(",")[0].strip()
            full_fips = city_to_fips.get(city_clean)

            if not full_fips:
                results.append(
                    {
                        "City": city_clean,
                        "Status": "County FIPS mapping not found for Census API.",
                    }
                )
                continue

            state_fips = full_fips[:2]
            county_fips = full_fips[2:]

            # Variables: DP02_0068E (Education Attainment - Bachelor's or Higher)
            # Dataset: ACS 1-Year Data Profiles (2022/2023)
            url = (
                f"https://api.census.gov/data/2023/acs/acs1/profile?get=NAME,DP02_0068PE"
                f"&for=county:{county_fips}&in=state:{state_fips}&key={census_key}"
            )

            response = requests.get(url, timeout=12)
            if response.status_code == 200:
                data = response.json()
                if len(data) > 1:
                    row = data[1]
                    pct = row[1]
                    name = row[0]
                    results.append(
                        {
                            "City": city_clean,
                            "Geography": name,
                            "Metric": "Bachelor's Degree or Higher (%)",
                            "Value": f"{pct}%",
                            "Source": "U.S. Census Bureau ACS (DP02 2023)",
                        }
                    )
                else:
                    results.append(
                        {
                            "City": city_clean,
                            "Status": "Census returned empty dataset.",
                        }
                    )
            else:
                results.append(
                    {
                        "City": city_clean,
                        "Status": f"Census API Failure ({response.status_code})",
                    }
                )

        return json.dumps(results, indent=2)

    except Exception as e:
        return json.dumps({"ERROR": str(e)}, indent=2)
