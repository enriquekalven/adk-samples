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

"""Offline hardening tests for recipe tools (no real HTTP, no .env)."""

import json
from unittest.mock import MagicMock

import pytest
import requests

import economic_research.tools.dynamic_search_harvester as harvester
import economic_research.tools.workforce_exposure_skill as workforce
from economic_research.shared_libraries import helper
from economic_research.tools import (
    census_skill,
    eia_skill,
    fec_skill,
    hud_skill,
    sentiment_skill,
)
from economic_research.tools.common import bureau_of_labor

SECRET = "SECRETKEY123"
LEAKY_MESSAGE = (
    "HTTPSConnectionPool(host='api.example.gov', port=443): Max retries "
    f"exceeded with url: /data?api_key={SECRET}&key={SECRET}"
    f"&apiKey={SECRET}"
)


@pytest.fixture(autouse=True)
def _isolated_session_keys():
    """Ensures no session-scoped API keys leak in from other tests."""
    token = helper._SESSION_API_KEYS.set(None)
    yield
    helper._SESSION_API_KEYS.reset(token)


def _raise_leaky(*args, **kwargs):
    raise requests.exceptions.ConnectionError(LEAKY_MESSAGE)


def _response(status=200, payload=None, json_error=None, text=""):
    resp = MagicMock()
    resp.status_code = status
    resp.text = text
    if json_error is not None:
        resp.json.side_effect = json_error
    else:
        resp.json.return_value = payload
    return resp


# --- M1: API keys never leak into error text -------------------------------


@pytest.mark.parametrize(
    ("env_name", "call"),
    [
        (
            "CENSUS_API_KEY",
            lambda: census_skill.fetch_census_education_stats(["Austin, TX"]),
        ),
        (
            "EIA_API_KEY",
            lambda: eia_skill.fetch_state_electricity_rates(["TX"]),
        ),
        ("FEC_API_KEY", lambda: fec_skill.analyze_political_stability("TX")),
        (
            "NEWS_API_KEY",
            lambda: sentiment_skill.analyze_market_sentiment("Austin jobs"),
        ),
    ],
)
def test_api_key_not_leaked_on_request_error(monkeypatch, env_name, call):
    monkeypatch.setenv(env_name, SECRET)
    monkeypatch.setattr(requests, "get", _raise_leaky)

    result = call()

    assert SECRET not in result
    assert "REDACTED" in result or "ConnectionError" in result


# --- L2: Census sentinels and non-JSON bodies ------------------------------


def test_census_sentinel_renders_na(monkeypatch):
    monkeypatch.setenv("CENSUS_API_KEY", "test-census-key")
    payload = [
        ["NAME", "DP02_0068PE", "state", "county"],
        ["Travis County, Texas", "-888888888", "48", "453"],
    ]
    monkeypatch.setattr(
        requests, "get", lambda *a, **k: _response(payload=payload)
    )

    data = json.loads(census_skill.fetch_census_education_stats(["Austin"]))

    assert data[0]["Value"] == "N/A"
    assert "-888888888%" not in json.dumps(data)
    assert "not available" in data[0]["Note"]


def test_census_valid_value_keeps_percentage(monkeypatch):
    monkeypatch.setenv("CENSUS_API_KEY", "test-census-key")
    payload = [
        ["NAME", "DP02_0068PE", "state", "county"],
        ["Travis County, Texas", "58.2", "48", "453"],
    ]
    monkeypatch.setattr(
        requests, "get", lambda *a, **k: _response(payload=payload)
    )

    data = json.loads(census_skill.fetch_census_education_stats(["Austin"]))

    assert data[0]["Value"] == "58.2%"
    assert "Note" not in data[0]


def test_census_non_json_body_is_per_city_error(monkeypatch):
    monkeypatch.setenv("CENSUS_API_KEY", "test-census-key")
    html = _response(json_error=ValueError("Expecting value"))
    monkeypatch.setattr(requests, "get", lambda *a, **k: html)

    data = json.loads(
        census_skill.fetch_census_education_stats(["Austin", "Seattle", "Oz"])
    )

    assert isinstance(data, list)
    assert len(data) == 3
    assert "non-JSON" in data[0]["Status"]
    assert "non-JSON" in data[1]["Status"]
    assert "mapping not found" in data[2]["Status"]


# --- L3: EIA null price ----------------------------------------------------


def test_eia_null_price_renders_na(monkeypatch):
    monkeypatch.setenv("EIA_API_KEY", "test-eia-key")
    payload = {"response": {"data": [{"price": None, "period": "2024-01"}]}}
    monkeypatch.setattr(
        requests, "get", lambda *a, **k: _response(payload=payload)
    )

    data = json.loads(eia_skill.fetch_state_electricity_rates(["TX", "CA"]))

    assert len(data) == 2
    assert data[0]["Avg Price (cents/kWh)"] == "N/A"
    assert data[0]["Period"] == "2024-01"


# --- L4: FEC state validation and DEMO_KEY label ---------------------------


@pytest.mark.parametrize("bad_state", ["", "Texas", "ZZ", "T1", "   "])
def test_fec_invalid_state_rejected(monkeypatch, bad_state):
    get = MagicMock()
    monkeypatch.setattr(requests, "get", get)

    data = json.loads(fec_skill.analyze_political_stability(bad_state))

    assert "ERROR" in data
    assert "Invalid state_abbr" in data["ERROR"]
    get.assert_not_called()


def test_fec_demo_key_is_labelled(monkeypatch):
    monkeypatch.delenv("FEC_API_KEY", raising=False)
    get = MagicMock(
        return_value=_response(payload={"results": [{"receipts": 1000.0}]})
    )
    monkeypatch.setattr(requests, "get", get)

    data = json.loads(fec_skill.analyze_political_stability(" tx "))

    assert get.call_args.kwargs["params"]["api_key"] == "DEMO_KEY"
    assert data["State"] == "TX"
    assert "DEMO_KEY" in data["Note"]
    assert "rate-limited" in data["Note"]


def test_fec_configured_key_has_no_demo_note(monkeypatch):
    monkeypatch.setenv("FEC_API_KEY", "real-fec-key")
    monkeypatch.setattr(
        requests,
        "get",
        lambda *a, **k: _response(payload={"results": [{"receipts": None}]}),
    )

    data = json.loads(fec_skill.analyze_political_stability("DC"))

    assert "Note" not in data
    assert data["Total Contributions"] == "$0.00"


# --- L1: HUD city suffix and household size --------------------------------


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("Austin", "48453"),
        ("Austin, TX", "48453"),
        ("  austin , texas ", "48453"),
        ("Austin-Round Rock, TX", "48453"),
        ("48453", "48453"),
        ("Portland, ME", "Portland, ME"),
        ("Columbus, GA", "Columbus, GA"),
    ],
)
def test_resolve_county_fips(value, expected):
    assert hud_skill.resolve_county_fips(value) == expected


def _hud_router(url, *args, **kwargs):
    if "/fmr/" in url:
        return _response(
            payload={
                "data": {
                    "county_name": "Travis County",
                    "basicdata": {"Two-Bedroom": "1800"},
                }
            }
        )
    if "/il/" in url:
        return _response(
            payload={
                "data": {
                    "county_name": "Travis County",
                    "very_low": {"il50_p1": "40000", "il50_p3": "51000"},
                }
            }
        )
    return _response(status=404)


def test_hud_fmr_resolves_city_with_state_suffix(monkeypatch):
    monkeypatch.setenv("HUD_API_KEY", "test-hud-key")
    get = MagicMock(side_effect=_hud_router)
    monkeypatch.setattr(requests, "get", get)

    data = json.loads(hud_skill.fetch_hud_fmr_data("Austin, TX"))

    assert data["Rent_2BR"] == "$1,800"
    assert "4845399999" in get.call_args.args[0]


def test_hud_affordability_uses_three_person_household(monkeypatch):
    monkeypatch.setenv("HUD_API_KEY", "test-hud-key")
    monkeypatch.setattr(requests, "get", _hud_router)

    data = json.loads(hud_skill.analyze_housing_affordability("Austin, TX"))

    # 51,000 / 12 = 4,250 (3-person), not 40,000 / 12 (1-person).
    assert data["Monthly_Income_50_AMI"] == "$4,250.00"
    assert data["Rent_to_Income_Ratio"] == "42.4%"
    assert "3 persons" in data["Household_Size_Basis"]


def test_hud_income_limits_default_household_is_one(monkeypatch):
    monkeypatch.setenv("HUD_API_KEY", "test-hud-key")
    monkeypatch.setattr(requests, "get", _hud_router)

    data = json.loads(hud_skill.fetch_hud_income_limits("48453"))

    assert data["AMI_50_Level"] == "$40,000"
    assert data["Household_Size"] == 1

    bad = json.loads(hud_skill.fetch_hud_income_limits("48453", 9))
    assert "ERROR" in bad


# --- L6/M11/L7: workforce exposure -----------------------------------------


@pytest.mark.parametrize("occupations", [[], [""], ["   "]])
def test_workforce_empty_occupation_errors(monkeypatch, occupations):
    monkeypatch.setenv("ONET_API_KEY", "")

    data = json.loads(workforce.analyze_workforce_exposure(occupations))

    assert "ERROR" in data


def test_workforce_blank_entry_does_not_match_first_db_entry(monkeypatch):
    monkeypatch.setenv("ONET_API_KEY", "")

    data = json.loads(
        workforce.analyze_workforce_exposure(["", "Software Developers", "a"])
    )

    assert "ERROR" in data[0]
    assert "soc" not in data[0]
    assert data[1]["soc"] == "15-1252"
    assert helper.SANDBOX_SOURCE in data[1]["source"]
    assert "Live" not in data[1]["source"]
    # A single letter must not substring-match "software developers".
    assert data[2]["exposure_level"] == "Unknown/Fuzzy Match"


def test_workforce_reads_onet_key_from_session(monkeypatch):
    monkeypatch.setenv("ONET_API_KEY", "")
    helper.set_session_api_key("ONET_API_KEY", "SESSION-ONET-KEY")
    get = MagicMock(return_value=_response(status=500))
    monkeypatch.setattr(requests, "get", get)

    data = json.loads(
        workforce.analyze_workforce_exposure(["Software Developers"])
    )

    assert get.call_args.kwargs["headers"]["X-API-Key"] == "SESSION-ONET-KEY"
    # Live fetch failed, so the curated estimate is used and labelled.
    assert helper.SANDBOX_SOURCE in data[0]["source"]
    assert "SESSION-ONET-KEY" not in json.dumps(data)


def test_workforce_gemini_failure_is_not_presented_as_rating(monkeypatch):
    monkeypatch.setenv("ONET_API_KEY", "test-onet-key")

    def router(url, *args, **kwargs):
        if url.endswith("/search"):
            return _response(
                payload={
                    "occupation": [
                        {"code": "15-1252.00", "title": "Software Developers"}
                    ]
                }
            )
        return _response(payload={"task": [{"title": "Write code"}]})

    monkeypatch.setattr(requests, "get", router)

    def boom(*args, **kwargs):
        raise RuntimeError(f"auth failed key={SECRET}")

    monkeypatch.setattr(workforce.genai, "Client", boom)

    data = json.loads(
        workforce.analyze_workforce_exposure(["Software Developers"])
    )

    assert data[0]["soc"] == "15-1252.00"
    assert data[0]["exposure_level"].startswith("Unknown")
    assert "unavailable" in data[0]["source"]
    assert "Live" not in data[0]["source"]
    assert SECRET not in json.dumps(data)


# --- Harvester fallbacks are never labelled live ---------------------------


def test_harvester_fallback_is_labelled_sandbox(monkeypatch):
    monkeypatch.setattr(harvester, "execute_serper_search", lambda q: "{}")

    res = harvester.harvest_real_estate_roi("Austin, TX")

    assert res["Avg Lease (PSF)"] == "$32.00"
    assert helper.SANDBOX_SOURCE in res["Source"]
    assert "Live" not in res["Source"]


def test_harvester_partial_fallback_names_estimated_fields(monkeypatch):
    monkeypatch.setattr(harvester, "execute_serper_search", lambda q: "x" * 100)
    client = MagicMock()
    client.return_value.models.generate_content.return_value.text = json.dumps(
        {"Overall Risk Rating": "Very High"}
    )
    monkeypatch.setattr(harvester.genai, "Client", client)

    res = harvester.harvest_climate_risk("Miami")

    assert res["Overall Risk Rating"] == "Very High"
    assert "NOT live" in res["Source"]
    assert "Primary Hazard (Heat)" in res["Source"]


# --- L8: bureau_of_labor is empty-safe and JSON-safe -----------------------


def test_union_employment_empty_mock_does_not_raise():
    rows, citations = bureau_of_labor.get_union_employment(
        [{"state": "Texas", "state_abbreviation": "TX"}]
    )

    assert rows == []
    assert citations == []


def test_bureau_of_labor_returns_json_safe_values():
    rows, citations = bureau_of_labor.get_labor_force_stats(["Austin"])
    wages, wage_citations = bureau_of_labor.get_median_hourly_wage(["Seattle"])

    json.dumps([rows, citations, wages, wage_citations])
    assert isinstance(rows, list)
    assert isinstance(citations, list)
    assert rows[0]["city_name"] == "Austin"
    assert "source" not in rows[0]
