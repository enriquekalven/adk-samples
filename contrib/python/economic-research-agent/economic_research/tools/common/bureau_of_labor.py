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

"""Bureau of Labor statistics functions (Internal Tool Logic).

Every function returns JSON-safe values: a ``(rows, citations)`` tuple where
``rows`` is a ``list[dict]`` and ``citations`` a sorted ``list[str]``. When
the backing query returns no data (or lacks the expected columns) both are
empty lists instead of raising ``KeyError``.
"""

import os
import re
from typing import Any

import pandas as pd

from economic_research.shared_libraries.helper import execute_bq_query_to_df

PROJECT_ID = os.getenv("PROJECT_ID") or ""
LABOR_STATS_DATASET = os.getenv("LABOR_STATS_DATASET") or ""


def _has_columns(df: pd.DataFrame | None, *columns: str) -> bool:
    return (
        df is not None
        and not df.empty
        and all(c in df.columns for c in columns)
    )


def _to_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Converts a DataFrame to JSON-safe records (NaN -> None)."""
    return df.astype(object).where(pd.notna(df), None).to_dict("records")


def _citations(df: pd.DataFrame) -> list[str]:
    return sorted(str(s) for s in df["source"].dropna().unique())


def _city_regex(city_names_lower: list[str]) -> str:
    return "|".join(re.escape(city) for city in city_names_lower)


def get_labor_force_stats(
    city_names: list[str],
) -> tuple[list[dict[str, Any]], list[str]]:
    """Get labor force stats from a city."""
    city_name_lower_case = [city_name.lower() for city_name in city_names]
    city_names_regex = _city_regex(city_name_lower_case)

    labor_query = """
    SELECT
        area_name,
        labor_force,
        CONCAT(unemployment_rate, '% (', date, ')') AS unemployment_rate,
        source
    FROM labor_force
    WHERE REGEXP_CONTAINS(
        LOWER(area_name),
        @city_names_regex
    );
    """

    labor_force_stats = execute_bq_query_to_df(
        project=PROJECT_ID,
        query=labor_query,
        params={
            "dataset": LABOR_STATS_DATASET,
            "city_names_regex": city_names_regex,
        },
    )
    if not _has_columns(labor_force_stats, "area_name", "source"):
        return [], []

    def find_city(area_name):
        area_name_lower = str(area_name).lower()
        for city in city_name_lower_case:
            if city in area_name_lower:
                return city.capitalize()
        return None

    labor_force_stats["city_name"] = labor_force_stats["area_name"].apply(
        find_city
    )

    # Citations.
    citations = _citations(labor_force_stats)

    # Drop citation column.
    labor_force_stats = labor_force_stats.drop(columns=["source", "area_name"])
    return _to_records(labor_force_stats), citations


def _merge_state_results(
    bq_results: pd.DataFrame,
    metros: list[dict[str, Any]],
    drop_state: bool,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Joins per-state query results onto metros; empty-safe."""
    if not _has_columns(bq_results, "state", "source"):
        return [], []

    metro_df = pd.DataFrame(metros)
    if "state" in metro_df.columns:
        merged = pd.merge(
            left=bq_results, right=metro_df, on="state", how="left"
        )
    else:
        merged = bq_results.copy()

    # Citations.
    citations = _citations(bq_results)

    labels_to_drop = ["source"]
    if drop_state:
        labels_to_drop.extend(["state", "state_abbreviation"])
    merged = merged.drop(columns=labels_to_drop, errors="ignore")
    return _to_records(merged), citations


def get_state_tax_rates(
    metros: list[dict[str, Any]], drop_state: bool = True
) -> tuple[list[dict[str, Any]], list[str]]:
    """Get State Tax Rates"""
    states = [metro.get("state", "") for metro in metros]

    state_tax_query = """
    SELECT
        state,
        CONCAT(tax_rate, '% (', year, ')') AS tax_rate,
        source
    FROM state_tax_rates
    WHERE state IN UNNEST(@states)
    """

    state_tax_bq_results = execute_bq_query_to_df(
        project=PROJECT_ID,
        query=state_tax_query,
        params={"dataset": LABOR_STATS_DATASET, "states": states},
    )

    return _merge_state_results(state_tax_bq_results, metros, drop_state)


def get_union_employment(
    metros: list[dict[str, Any]], drop_state: bool = True
) -> tuple[list[dict[str, Any]], list[str]]:
    """Get Union Employment Percentage"""
    states = [metro.get("state", "") for metro in metros]

    union_employement_query = """
    SELECT
        state,
        CONCAT(union_employed, '% (', year, ')') AS union_employed,
        source
    FROM union_employed
    WHERE state IN UNNEST(@states)
    """

    state_union_employement = execute_bq_query_to_df(
        project=PROJECT_ID,
        query=union_employement_query,
        params={"dataset": LABOR_STATS_DATASET, "states": states},
    )

    return _merge_state_results(state_union_employement, metros, drop_state)


def get_median_hourly_wage(
    city_names: list[str],
) -> tuple[list[dict[str, Any]], list[str]]:
    """Get median hourly wages from a city."""
    city_name_lower_case = [city_name.lower() for city_name in city_names]
    city_names_regex = _city_regex(city_name_lower_case)

    median_wage_query = """
    SELECT
        metro,
        CONCAT('$',median_hourly_wage) AS median_hourly_wage,
        source
    FROM metro_median_hourly_wages
    WHERE REGEXP_CONTAINS(
        LOWER(metro),
        @city_names_regex
    );
    """

    median_hourly_wages = execute_bq_query_to_df(
        project=PROJECT_ID,
        query=median_wage_query,
        params={
            "dataset": LABOR_STATS_DATASET,
            "city_names_regex": city_names_regex,
        },
    )
    if not _has_columns(median_hourly_wages, "metro", "source"):
        return [], []

    def find_city(metro):
        metro_lower = str(metro).lower()
        for city in city_name_lower_case:
            if city in metro_lower:
                return city.capitalize()
        return None

    median_hourly_wages["city_name"] = median_hourly_wages["metro"].apply(
        find_city
    )

    # Citations.
    citations = _citations(median_hourly_wages)

    # Drop citation column.
    median_hourly_wages = median_hourly_wages.drop(columns=["source", "metro"])
    return _to_records(median_hourly_wages), citations
