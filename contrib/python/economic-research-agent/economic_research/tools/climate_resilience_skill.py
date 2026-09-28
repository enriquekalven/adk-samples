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

"""ADK Skill: Climate Risk & Resilience (FEMA NRI). 20-year investment protection."""

import json

from pydantic import BaseModel, Field

from economic_research.tools.dynamic_search_harvester import (
    harvest_climate_risk,
)


class ClimateRequest(BaseModel):
    city_names: list[str] = Field(
        ..., description="List of cities to fetch climate risk benchmarks for."
    )


def get_climate_risk_index(city_names: list[str]) -> str:
    """
    Fetches FEMA National Risk Index (NRI) benchmarks for MSAs.
    Analyzes 18 natural hazards (Heat, Flood, Hurricane) to protect 20-year infrastructure investments.
    """
    results = []

    for city in city_names:
        city_clean = city.split(",")[0].strip()
        harvested = harvest_climate_risk(city_clean)
        results.append(harvested)

    return json.dumps(results, indent=2)
