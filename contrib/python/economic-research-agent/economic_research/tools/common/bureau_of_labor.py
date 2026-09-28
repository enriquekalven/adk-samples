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

"""Bureau of Labor statistics functions (Internal Tool Logic)."""

import os
from typing import Any

import pandas as pd

from economic_research.shared_libraries.helper import execute_bq_query_to_df

PROJECT_ID = os.getenv("PROJECT_ID") or "economic-research-agent"
LABOR_STATS_DATASET = os.getenv("LABOR_STATS_DATASET") or "bls"


def get_labor_force_stats(city_names: list[str]):
    """Get labor force stats from a city."""
    labor_force_table = "labor_force"

    city_name_lower_case = [city_name.lower() for city_name in city_names]
    city_names_regex = "|".join(city_name_lower_case)

    column_name_to_match = "area_name"

    labor_query = f"""
    SELECT
        area_name,
        labor_force,
        CONCAT(unemployment_rate, '% (', date, ')') AS unemployment_rate,
        source
    FROM `{PROJECT_ID}.{LABOR_STATS_DATASET}.{labor_force_table}`
    WHERE REGEXP_CONTAINS(
        LOWER({column_name_to_match}),
        '{city_names_regex}'
    );
    """  # noqa: S608

    labor_force_stats = execute_bq_query_to_df(
        project=PROJECT_ID, query=labor_query
    )

    def find_city(area_name):
        area_name_lower = area_name.lower()
        for city in city_name_lower_case:
            if city in area_name_lower:
                return city.capitalize()
        return None

    labor_force_stats["city_name"] = labor_force_stats["area_name"].apply(
        find_city
    )

    # Citations.
    citations = set(labor_force_stats["source"].unique())

    # Drop citation column.
    labor_force_stats.drop(["source", "area_name"], inplace=True, axis=1)
    return labor_force_stats, citations


def get_state_tax_rates(metros: list[dict[str, Any]], drop_state: bool = True):
    """Get State Tax Rates"""
    state_tax_table = "state_tax_rates"

    states = [metro.get("state", "") for metro in metros]

    column_name_to_match = "state"

    state_tax_query = f"""
    SELECT
        state,
        CONCAT(tax_rate, '% (', year, ')') AS tax_rate,
        source
    FROM `{PROJECT_ID}.{LABOR_STATS_DATASET}.{state_tax_table}`
    WHERE {column_name_to_match} IN UNNEST({states})
    """  # noqa: S608

    state_tax_bq_results = execute_bq_query_to_df(
        project=PROJECT_ID, query=state_tax_query
    )

    if state_tax_bq_results.empty:
        return pd.DataFrame(), []

    metro_df = pd.DataFrame(metros)

    state_tax_df = pd.merge(
        left=state_tax_bq_results, right=metro_df, on="state", how="left"
    )

    # Citations.
    citations = set(state_tax_bq_results["source"].unique())

    labels_to_drop = ["source"]
    if drop_state:
        labels_to_drop.extend(["state", "state_abbreviation"])

    state_tax_df.drop(labels=labels_to_drop, axis=1, inplace=True)

    return state_tax_df, citations


def get_union_employment(metros: list[dict[str, Any]], drop_state: bool = True):
    """Get Union Employment Percentage"""
    union_table = "union_employed"

    states = [metro.get("state", "") for metro in metros]

    column_name_to_match = "state"

    union_employement_query = f"""
    SELECT
        state,
        CONCAT(union_employed, '% (', year, ')') AS union_employed,
        source
    FROM `{PROJECT_ID}.{LABOR_STATS_DATASET}.{union_table}`
    WHERE {column_name_to_match} IN UNNEST({states})
    """  # noqa: S608

    state_union_employement = execute_bq_query_to_df(
        project=PROJECT_ID, query=union_employement_query
    )

    metro_df = pd.DataFrame(metros)

    union_employment_df = pd.merge(
        left=state_union_employement, right=metro_df, on="state", how="left"
    )

    # Citations.
    citations = set(state_union_employement["source"].unique())

    labels_to_drop = ["source"]
    if drop_state:
        labels_to_drop.extend(["state", "state_abbreviation"])
    union_employment_df.drop(labels=labels_to_drop, axis=1, inplace=True)

    return union_employment_df, citations


def get_median_hourly_wage(city_names: list[str]):
    """Get median hourly wages from a city."""
    median_hourly_wage_table = "metro_median_hourly_wages"

    city_name_lower_case = [city_name.lower() for city_name in city_names]

    city_names_regex = "|".join(city_name_lower_case)

    column_name_to_match = "metro"

    median_wage_query = f"""
    SELECT
        metro,
        CONCAT('$',median_hourly_wage) AS median_hourly_wage,
        source
    FROM `{PROJECT_ID}.{LABOR_STATS_DATASET}.{median_hourly_wage_table}`
    WHERE REGEXP_CONTAINS(
        LOWER({column_name_to_match}),
        '{city_names_regex}'
    );
    """  # noqa: S608

    median_hourly_wages = execute_bq_query_to_df(
        project=PROJECT_ID, query=median_wage_query
    )

    def find_city(metro):
        metro_lower = metro.lower()
        for city in city_name_lower_case:
            if city in metro_lower:
                return city.capitalize()
        return None

    median_hourly_wages["city_name"] = median_hourly_wages["metro"].apply(
        find_city
    )

    # Citations.
    citations = set(median_hourly_wages["source"].unique())

    # Drop citation column.
    median_hourly_wages.drop(["source", "metro"], inplace=True, axis=1)
    return median_hourly_wages, citations
