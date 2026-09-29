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

"""Unit tests for Dynamic routing and self-measurement of economic primitives."""

import glob
import json
import os
import shutil
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from economic_research.audit_loop import DRAFT_KEY, REVISIONS_KEY, VERDICT_KEY
from economic_research.shared_libraries.helper import KNOWN_API_KEYS


@pytest.fixture(autouse=True)
def mock_keys(monkeypatch):
    """Mock all API keys in environment to prevent get_cloud_secret calling gcloud/metadata credentials."""
    for key in KNOWN_API_KEYS:
        monkeypatch.setenv(key, f"mock_{key.lower()}")


def _clear_observability_dir() -> str:
    import tempfile

    env_log_dir = os.getenv("OBSERVABILITY_LOG_DIR")
    log_dir = (
        env_log_dir
        if env_log_dir and not env_log_dir.startswith("<TODO:")
        else os.path.join(tempfile.gettempdir(), "observability")
    )
    if os.path.exists(log_dir):
        shutil.rmtree(log_dir)
    return log_dir


def _run_query_with_scripted_apps(question, app_results, monkeypatch):
    """Runs ERAAgent.query() with each ADK app run replaced by a script.

    query() makes three app runs, in order: the complexity router, the main
    (audited) research app and the primitives evaluator. Each item of
    ``app_results`` is the ``(text, session_state)`` for one run.

    Returns the report and the model names passed to get_app().
    """
    from economic_research.agent import ERAAgent, export_agent

    monkeypatch.delenv("ERA_BYPASS_SUPERVISOR", raising=False)
    requested_models = []
    real_get_app = ERAAgent.get_app

    def spy_get_app(self, model_name=None):
        requested_models.append(model_name)
        return real_get_app(self, model_name=model_name)

    with (
        patch.object(ERAAgent, "get_app", spy_get_app),
        patch.object(
            ERAAgent, "_run_app", AsyncMock(side_effect=app_results)
        ) as run_app,
    ):
        report = export_agent.query(question)
    assert run_app.await_count == len(app_results)
    return report, requested_models


def test_query_routing_and_primitives_low_complexity(monkeypatch):
    log_dir = _clear_observability_dir()
    monkeypatch.setenv("MODEL_NAME", "gemini-3.5-flash")
    monkeypatch.setenv("MODEL_NAME_GENERATED_1", "gemini-3.1-pro")

    draft = "This is a simple report on Ohio electricity rates."
    result, models = _run_query_with_scripted_apps(
        "What is the electricity rate in Ohio?",
        [
            ('{"complexity": "LOW"}', {}),
            (
                draft,
                {
                    DRAFT_KEY: draft,
                    VERDICT_KEY: "[APPROVE] Audit: No hallucinations found. PASSED.",
                    REVISIONS_KEY: 0,
                },
            ),
            (
                '{"interaction_type": "directive", "autonomy_level": 2, "human_only_time_minutes": 10, "human_education_years_required": 12, "task_success": true}',
                {},
            ),
        ],
        monkeypatch,
    )

    # LOW complexity keeps the default model for the research run.
    assert models == ["gemini-3.5-flash"]
    assert draft in result
    assert "Auditor Judge Verification (Passed v1)" in result
    assert "PASSED" in result

    log_files = glob.glob(os.path.join(log_dir, "*.json"))
    assert len(log_files) == 1

    with open(log_files[0]) as f:
        log_data = json.load(f)
        assert log_data["query"] == "What is the electricity rate in Ohio?"
        assert log_data["primitives"]["interaction_type"] == "directive"
        assert log_data["primitives"]["autonomy_level"] == 2
        assert log_data["primitives"]["human_only_time_minutes"] == 10
        assert log_data["primitives"]["human_education_years_required"] == 12
        assert log_data["primitives"]["task_success"] is True


def test_query_routing_and_primitives_high_complexity_with_rejection(
    monkeypatch,
):
    log_dir = _clear_observability_dir()
    monkeypatch.setenv("MODEL_NAME", "gemini-3.5-flash")
    monkeypatch.setenv("MODEL_NAME_GENERATED_1", "gemini-3.1-pro")

    # The audited loop already revised the draft once after a [REJECT];
    # its session state carries the corrected draft and revision count.
    corrected = "Austin vs Raleigh: Austin is better."
    result, models = _run_query_with_scripted_apps(
        "Compare Austin and Raleigh for a new tech hub.",
        [
            ('{"complexity": "HIGH"}', {}),
            (
                "Austin is better. [REJECT] Missing Raleigh comparison data. "
                + corrected,
                {
                    DRAFT_KEY: corrected,
                    VERDICT_KEY: "[APPROVE] Raleigh comparison now included.",
                    REVISIONS_KEY: 1,
                },
            ),
            (
                '{"interaction_type": "task_iteration", "autonomy_level": 4, "human_only_time_minutes": 120, "human_education_years_required": 16, "task_success": true}',
                {},
            ),
        ],
        monkeypatch,
    )

    # HIGH complexity routes the research run to MODEL_NAME_GENERATED_1.
    assert models == ["gemini-3.1-pro"]
    # The final report is the corrected draft, not the raw event stream.
    assert result.startswith(corrected)
    assert "Self-Corrected v2" in result
    assert "Raleigh comparison now included" in result

    log_files = glob.glob(os.path.join(log_dir, "*.json"))
    assert len(log_files) == 1

    with open(log_files[0]) as f:
        log_data = json.load(f)
        assert log_data["primitives"]["interaction_type"] == "task_iteration"
        assert log_data["primitives"]["autonomy_level"] == 4
        assert log_data["primitives"]["human_only_time_minutes"] == 120
        assert log_data["primitives"]["human_education_years_required"] == 16
        assert log_data["primitives"]["task_success"] is True


def test_query_falls_back_to_default_model_on_quota(monkeypatch):
    monkeypatch.setenv("MODEL_NAME", "gemini-3.5-flash")
    monkeypatch.setenv("MODEL_NAME_GENERATED_1", "gemini-3.1-pro")

    result, models = _run_query_with_scripted_apps(
        "Compare Austin and Raleigh.",
        [
            ('{"complexity": "HIGH"}', {}),
            RuntimeError("429 RESOURCE_EXHAUSTED"),
            ("Fallback report.", {DRAFT_KEY: "Fallback report."}),
            ("not json", {}),  # evaluator failure must not break query()
        ],
        monkeypatch,
    )

    assert models == ["gemini-3.1-pro", "gemini-3.5-flash"]
    assert result == "Fallback report."


def test_analyze_workforce_exposure(monkeypatch):
    monkeypatch.setenv("ONET_API_KEY", "")
    from economic_research.tools.workforce_exposure_skill import (
        analyze_workforce_exposure,
    )

    result = analyze_workforce_exposure(
        ["Software Developers", "Customer Service Representatives"]
    )
    data = json.loads(result)

    assert len(data) == 2
    assert data[0]["exposure_level"] == "High"
    assert "Augmentation" in data[0]["impact_mode"]
    assert "Writing/refactoring code" in data[0]["key_exposed_tasks"]

    assert data[1]["exposure_level"] == "High"
    assert "Automation" in data[1]["impact_mode"]

    result_unknown = analyze_workforce_exposure(["Astronaut"])
    data_unknown = json.loads(result_unknown)
    assert data_unknown[0]["exposure_level"] == "Unknown/Fuzzy Match"


def test_fetch_anthropic_economic_index_data():
    from economic_research.tools.economic_index_skill import (
        fetch_anthropic_economic_index_data,
    )

    result_model = fetch_anthropic_economic_index_data("model_selection")
    data_model = json.loads(result_model)
    assert "shares_by_domain" in data_model
    assert data_model["average_overall_opus_share"] == "51%"

    result_tenure = fetch_anthropic_economic_index_data("user_tenure")
    data_tenure = json.loads(result_tenure)
    assert "comparison" in data_tenure
    assert (
        data_tenure["comparison"]["personal_use_share"]["high_tenure"] == "38%"
    )

    result_invalid = fetch_anthropic_economic_index_data("invalid_type")
    data_invalid = json.loads(result_invalid)
    assert "error" in data_invalid


def test_fetch_mls_property_listings():
    from economic_research.tools.mls_property_analysis_skill import (
        fetch_mls_property_listings,
    )

    result = fetch_mls_property_listings("Columbus")
    data = json.loads(result)

    assert len(data) > 0
    assert data[0]["Property Type"] in ["Condo", "Single-family", "Multifamily"]
    assert "Estimated Cap Rate" in data[0]
    assert "Price-to-Rent Ratio" in data[0]

    result_invalid = fetch_mls_property_listings("NonexistentCity")
    data_invalid = json.loads(result_invalid)
    assert "status" in data_invalid
    assert data_invalid["status"] == "No listings found"


@patch("requests.get")
def test_fetch_hud_usps_crosswalk(mock_get):
    from economic_research.tools.hud_skill import fetch_hud_usps_crosswalk

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": {
            "results": [{"geoid": "48453", "zip": "78702", "res_ratio": "0.98"}]
        }
    }
    mock_get.return_value = mock_resp

    result = fetch_hud_usps_crosswalk("78702")
    data = json.loads(result)
    assert data["ZIP"] == "78702"
    assert data["County_FIPS"] == "48453"
    assert data["Residential_Ratio"] == "0.98"


@patch("requests.get")
def test_fetch_hud_chas_data(mock_get):
    from economic_research.tools.hud_skill import fetch_hud_chas_data

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [
        {
            "geoname": "Travis County",
            "A18": "100000",
            "B3": "30000",
            "D6": "10000",
            "D9": "15000",
        }
    ]
    mock_get.return_value = mock_resp

    result = fetch_hud_chas_data("48453")
    data = json.loads(result)
    assert data["Geography"] == "Travis County"
    assert data["Total_Households"] == "100,000"
    assert data["Households_With_Housing_Problems_Pct"] == "30.0%"
    assert data["Households_Cost_Burdened_Pct"] == "25.0%"


def test_model_labor_shifts(monkeypatch):
    monkeypatch.setenv("FRED_API_KEY", "")
    from economic_research.tools.labor_shift_skill import model_labor_shifts

    result = model_labor_shifts(["Austin", "Columbus"])
    data = json.loads(result)

    assert len(data) == 2
    assert data[0]["City"] == "Austin"
    assert data[0]["Vulnerability Index (0-100)"] == 35
    assert data[0]["Augmentation Potential (0-100)"] == 85

    assert data[1]["City"] == "Columbus"
    assert data[1]["Vulnerability Index (0-100)"] == 68

    result_unknown = model_labor_shifts(["Orlando"])
    data_unknown = json.loads(result_unknown)
    assert data_unknown[0]["Vulnerability Index (0-100)"] == 50


def test_run_econometric_regression():
    from economic_research.tools.econometrics_skill import (
        run_econometric_regression,
    )

    y = [1.0, 2.0, 3.0, 4.0, 5.0]
    x = [2.0, 4.0, 6.0, 8.0, 10.0]

    # Test OLS
    res_ols = run_econometric_regression(y, x, analysis_type="OLS")
    data_ols = json.loads(res_ols)
    assert data_ols["Analysis"] == "Ordinary Least Squares (OLS) Regression"
    assert data_ols["Observations"] == 5
    assert float(data_ols["R_Squared"]) == 1.0

    # Test Correlation
    res_corr = run_econometric_regression(y, x, analysis_type="correlation")
    data_corr = json.loads(res_corr)
    assert data_corr["Analysis"] == "Pearson Correlation Matrix"
    assert data_corr["Matrix"]["Y"]["Y"] == 1.0

    # Test ADF
    res_adf = run_econometric_regression(y, x, analysis_type="ADF")
    data_adf = json.loads(res_adf)
    assert (
        data_adf["Analysis"]
        == "Augmented Dickey-Fuller (ADF) Stationarity Test"
    )


def test_underwrite_deal_leverage():
    from economic_research.tools.underwriting_skill import (
        underwrite_deal_leverage,
    )

    result = underwrite_deal_leverage(
        purchase_price=1000000.0,
        rent_monthly=10000.0,
        down_payment_pct=25.0,
        interest_rate=6.0,
        operating_expenses_pct=40.0,
        vacancy_rate=5.0,
    )
    data = json.loads(result)
    assert data["Acquisition_Summary"]["Purchase_Price"] == "$1,000,000.00"
    assert data["Acquisition_Summary"]["Loan_Amount"] == "$750,000.00"
    assert data["Performance_Metrics"]["Unleveraged_Cap_Rate"] == "6.84%"
    assert data["Underwriting_Assumptions"]["Down_Payment_Pct"] == "25.0%"


def test_generate_location_scorecard():
    from economic_research.tools.scorecard_skill import (
        generate_location_scorecard,
    )

    result = generate_location_scorecard(["TX", "NC"])
    data = json.loads(result)
    assert "Scorecard_Summary" in data
    assert len(data["Scorecard_Summary"]) == 2
    assert data["Scorecard_Summary"][0]["State_Code"] in ["TX", "NC"]


def test_estimate_employee_relocation():
    from economic_research.tools.relocation_skill import (
        estimate_employee_relocation,
    )

    result = estimate_employee_relocation(
        "CA", "NC", "48453", "37183", 150000.0
    )
    data = json.loads(result)
    assert "Relocation_Comparison" in data
    assert (
        data["Annual_Cost_Analysis"]["Estimated_State_Income_Tax"]["Origin"]
        == "$19,950.00 (13.30%)"
    )


def test_search_macro_series():
    from economic_research.tools.macro_search_skill import search_macro_series

    result = search_macro_series("gdp")
    data = json.loads(result)
    assert data["Query"] == "gdp"
    assert data["Matches"][0]["series_id"] == "GDPC1"


@patch("requests.get")
def test_fetch_hud_fmr_data_city_fallback(mock_get):
    from economic_research.tools.hud_skill import fetch_hud_fmr_data

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": {"county_name": "Travis County", "basicdata": {"fmr_2": "1800"}}
    }
    mock_get.return_value = mock_resp

    # Call with "Austin" city fallback instead of "48453"
    result = fetch_hud_fmr_data("Austin")
    data = json.loads(result)
    assert data["Geography"] == "Travis County"
    assert data["Rent_2BR"] == "$1,800"


@patch("requests.get")
def test_analyze_political_stability(mock_get):
    from economic_research.tools.fec_skill import analyze_political_stability

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "results": [
            {
                "state": "TX",
                "cycle": 2024,
                "total": 50000000.0,
                "individual_total": 30000000.0,
                "pac_total": 20000000.0,
            }
        ]
    }
    mock_get.return_value = mock_resp

    result = analyze_political_stability("TX")
    data = json.loads(result)
    assert data["State"] == "TX"
    assert "Total Contributions" in data


def test_fetch_regional_trade_data(monkeypatch):
    monkeypatch.setenv("CENSUS_API_KEY", "")
    from economic_research.tools.trade_skill import fetch_regional_trade_data

    result = fetch_regional_trade_data(
        ["Texas", "California"], "Electronic Products"
    )
    data = json.loads(result)

    assert len(data) == 2
    assert data[0]["State"] == "Texas"
    assert data[0]["Commodity"] == "Electronic Products"
    assert "Top Import (Mexico)" in data[0]["Market Profile"]
    assert "Source" in data[0]
