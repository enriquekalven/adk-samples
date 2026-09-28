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

"""ADK Skill: Bureau of Labor Statistics (BLS). Hardened labor analytics."""

from typing import Any

from pydantic import BaseModel, Field

from .bls_functions import (
    find_labor_force_stats,
    find_median_hourly_wages,
    find_state_tax_rate,
    find_state_union_employment,
)


class CityNamesRequest(BaseModel):
    city_names: list[str] = Field(
        ..., min_length=1, description="List of city names."
    )


class StateNamesRequest(BaseModel):
    state_names: list[str] = Field(
        ..., min_length=1, description="List of full state names."
    )


def labor_force_stats_skill(city_names: list[str]) -> Any:
    """
    Fetches BLS data for labor force statistics (unemployment, labor force).
    """
    return find_labor_force_stats(city_names)


def median_hourly_wages_skill(city_names: list[str]) -> Any:
    """
    Fetches BLS data for median hourly wages across all occupations.
    """
    return find_median_hourly_wages(city_names)


def state_union_employment_skill(state_names: list[str]) -> Any:
    """
    Fetches state-level union employment rates.
    """
    return find_state_union_employment(state_names)


def state_tax_rate_skill(state_names: list[str]) -> Any:
    """
    Fetches state-level corporate income tax rates.
    """
    return find_state_tax_rate(state_names)
