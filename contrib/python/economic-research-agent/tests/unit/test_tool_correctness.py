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

"""Offline correctness tests for tool data handling.

Every network call is mocked; no test depends on `.env` or live APIs.
"""

import io
import json
import logging
from unittest.mock import MagicMock, patch

import pytest
import requests

from economic_research.shared_libraries.helper import (
    SANDBOX_SOURCE,
    init_session_api_keys,
    set_session_api_key,
)

_ALL_KEYS = (
    "BEA_API_KEY",
    "BLS_API_KEY",
    "CENSUS_API_KEY",
    "EIA_API_KEY",
    "FRED_API_KEY",
    "HUD_API_KEY",
    "RENTCAST_API_KEY",
    "SERPER_API_KEY",
)


@pytest.fixture(autouse=True)
def hermetic_env(monkeypatch):
    """No real keys from the shell / .env, and fresh session keys."""
    for key in _ALL_KEYS:
        monkeypatch.delenv(key, raising=False)
    init_session_api_keys()
    yield
    init_session_api_keys()


def _response(status=200, payload=None, text=""):
    resp = MagicMock(status_code=status, text=text)
    resp.json.return_value = payload
    return resp


def _bls_payload(value):
    return json.dumps(
        [
            {
                "Series ID": "X",
                "Current Value": f"{value} (August 2025)",
                "Status": "Success",
            }
        ]
    )


# --- H6 / H7 / H8: scorecard ---------------------------------------------


def _scorecard(states, tax, elec, unemployment, **kwargs):
    from economic_research.tools import scorecard_skill

    def fake_tax(names):
        return json.dumps([{"Corporate Tax Rate": tax.get(names[0], "N/A")}])

    def fake_elec(codes, sector="industrial"):
        code = codes[0]
        if code not in elec:
            return json.dumps([{"State": code, "Status": "No data"}])
        return json.dumps(
            [
                {
                    "State": code,
                    "Sector": "Industrial",
                    "Avg Price (cents/kWh)": elec[code],
                    "Period": "2025-06",
                }
            ]
        )

    def fake_bls(code):
        if code not in unemployment:
            return json.dumps({"ERROR": "unknown"})
        return _bls_payload(unemployment[code])

    with (
        patch.object(scorecard_skill, "fetch_state_tax_rates", fake_tax),
        patch.object(
            scorecard_skill, "fetch_state_electricity_rates", fake_elec
        ),
        patch.object(scorecard_skill, "analyze_labor_force_quality", fake_bls),
    ):
        result = json.loads(
            scorecard_skill.generate_location_scorecard(states, **kwargs)
        )
    return {r["State_Code"]: r for r in result["Scorecard_Summary"]}, result


def test_scorecard_parses_eia_avg_price_key():
    rows, _ = _scorecard(
        ["NC", "GA"],
        tax={"North Carolina": "2.5%", "Georgia": "5.39%"},
        elec={"NC": "7.85", "GA": "12.40 ¢/kWh"},
        unemployment={"NC": "3.7", "GA": "3.5"},
    )
    assert "7.85¢/kWh" in rows["NC"]["Criteria_Scores"]["Electricity_Rate"]
    assert "12.40¢/kWh" in rows["GA"]["Criteria_Scores"]["Electricity_Rate"]
    assert rows["NC"]["Criteria_Scores"]["Electricity_Rate"].startswith(
        "100.0/100"
    )
    assert "electricity_rate" not in rows["NC"]["Fallbacks_Used"]


def test_scorecard_marks_missing_electricity_as_fallback():
    rows, result = _scorecard(
        ["NC", "GA"],
        tax={"North Carolina": "2.5%", "Georgia": "5.39%"},
        elec={"NC": "8.00"},  # GA missing
        unemployment={"NC": "3.7", "GA": "3.5"},
    )
    ga = rows["GA"]
    assert "electricity_rate" in ga["Fallbacks_Used"]
    assert "[FALLBACK]" in ga["Criteria_Scores"]["Electricity_Rate"]
    assert "imputed" in ga["Data_Basis"]["Electricity_Rate"]
    assert "[FALLBACK]" in result["Methodology"]


def test_scorecard_no_corporate_income_tax_states_are_zero():
    rows, _ = _scorecard(
        ["TX", "WY", "CA"],
        # Even if the scrape says something odd, TX/WY have no CIT.
        tax={"Texas": "N/A", "Wyoming": "(b)", "California": "8.84%"},
        elec={"TX": "7", "WY": "7", "CA": "20"},
        unemployment={"TX": "4", "WY": "3", "CA": "5.5"},
    )
    assert "Tax Rate: 0.00%" in rows["TX"]["Criteria_Scores"]["Corporate_Tax"]
    assert "Tax Rate: 0.00%" in rows["WY"]["Criteria_Scores"]["Corporate_Tax"]
    assert "gross receipts" in rows["TX"]["Data_Basis"]["Corporate_Tax"]
    assert "Tax Rate: 8.84%" in rows["CA"]["Criteria_Scores"]["Corporate_Tax"]
    assert "corporate_tax" not in rows["TX"]["Fallbacks_Used"]


def test_parse_corporate_tax_rate_text():
    from economic_research.tools.scorecard_skill import _parse_corporate_tax

    assert _parse_corporate_tax("None (Gross Receipts Tax)") == 0.0
    assert _parse_corporate_tax("2.5%") == 2.5
    assert _parse_corporate_tax("0% / 2% / 9.4%") == 9.4
    assert _parse_corporate_tax("N/A (Check Source)") is None


def test_scorecard_unknown_tax_is_labelled_not_silent_default():
    rows, _ = _scorecard(
        ["NC", "GA"],
        tax={"North Carolina": "2.5%"},  # GA unknown
        elec={"NC": "8", "GA": "9"},
        unemployment={"NC": "3.7", "GA": "3.5"},
    )
    assert "corporate_tax" in rows["GA"]["Fallbacks_Used"]
    assert "[FALLBACK]" in rows["GA"]["Criteria_Scores"]["Corporate_Tax"]


def test_scorecard_labor_uses_bls_and_employer_perspective():
    kwargs = {
        "tax": {"North Carolina": "2.5%", "Georgia": "2.5%"},
        "elec": {"NC": "8", "GA": "8"},
        "unemployment": {"NC": "5.0", "GA": "3.0"},
    }
    employer, result = _scorecard(["NC", "GA"], **kwargs)
    worker, _ = _scorecard(["NC", "GA"], employer_perspective=False, **kwargs)
    # Employer view: more labor slack (higher unemployment) scores higher.
    assert employer["NC"]["Criteria_Scores"]["Labor_Quality"].startswith(
        "100.0/100"
    )
    assert worker["GA"]["Criteria_Scores"]["Labor_Quality"].startswith(
        "100.0/100"
    )
    assert "BLS LAUS" in employer["NC"]["Data_Basis"]["Labor_Quality"]
    assert "BLS LAUS" in result["Methodology"]


# --- H9 / M8: dynamic entity resolver ------------------------------------


def _fake_serper(text):
    def fake_urlopen(req, timeout=None):
        body = json.dumps({"organic": [{"snippet": text}]}).encode()
        return io.BytesIO(body)

    return fake_urlopen


def test_unresolved_place_is_not_austin():
    from economic_research.tools import dynamic_entity_resolver as r

    assert r.resolve_fips("Nowhereville") == r.UNRESOLVED
    assert r.resolve_fips(None) == r.UNRESOLVED
    assert r.resolve_fips([]) == r.UNRESOLVED
    assert r.resolve_msa_code("Nowhereville") == r.UNRESOLVED
    details = r.resolve_fips_details("Nowhereville")
    assert details["status"] == "unresolved"
    assert details["reason"]
    assert "48453" not in json.dumps(details)


def test_orange_county_ca_is_not_mapped_to_florida():
    from economic_research.tools import dynamic_entity_resolver as r

    assert r.resolve_fips("Orange County, CA") == r.UNRESOLVED
    assert r.resolve_fips("Orange County, FL") == "12095"
    assert r.resolve_fips("Orange County, Florida") == "12095"
    # Whole tokens only: no substring match onto "orange".
    assert r.resolve_fips("West Orange, NJ") == r.UNRESOLVED
    assert r.resolve_fips("Austin, TX") == "48453"
    assert r.resolve_fips("Miami-Dade County, FL") == "12086"
    assert r.resolve_msa_code("Columbus, GA") == r.UNRESOLVED
    assert r.resolve_msa_code("Columbus, OH") == "18140"


def test_serper_fips_is_validated_and_not_cached(monkeypatch):
    from economic_research.tools import dynamic_entity_resolver as r

    monkeypatch.setenv("SERPER_API_KEY", "serper-test-key")
    before = json.dumps(r.ENTITY_CACHE, sort_keys=True)
    text = "Orange County, CA 92701. FIPS code 06059. See also FIPS 12095."
    monkeypatch.setattr(r.urllib.request, "urlopen", _fake_serper(text))

    assert r.resolve_fips("Orange County, CA") == "06059"
    assert r.resolve_fips_details("Orange County, CA")["method"] == "serper"
    assert json.dumps(r.ENTITY_CACHE, sort_keys=True) == before


def test_serper_fips_with_wrong_state_or_zip_is_rejected(monkeypatch):
    from economic_research.tools import dynamic_entity_resolver as r

    monkeypatch.setenv("SERPER_API_KEY", "serper-test-key")
    text = "Springfield ZIP 92701; FIPS code 12095 (Florida)."
    monkeypatch.setattr(r.urllib.request, "urlopen", _fake_serper(text))

    assert r.resolve_fips("Springfield, CA") == r.UNRESOLVED
    # A bare ZIP-looking number without 'FIPS' context is ignored.
    monkeypatch.setattr(
        r.urllib.request, "urlopen", _fake_serper("Located at 06059 Main St")
    )
    assert r.resolve_fips("Springfield, CA") == r.UNRESOLVED


# --- M2: BLS ---------------------------------------------------------------


def test_bls_state_series_id_is_20_chars():
    from economic_research.tools import bls_api_skill

    payload = {
        "status": "REQUEST_SUCCEEDED",
        "Results": {
            "series": [
                {
                    "seriesID": "LASST480000000000003",
                    "data": [
                        {"value": "4.1", "periodName": "August", "year": "2025"}
                    ],
                }
            ]
        },
    }
    with patch.object(
        bls_api_skill.requests, "post", return_value=_response(200, payload)
    ) as mock_post:
        result = json.loads(bls_api_skill.analyze_labor_force_quality("tx"))

    sent = json.loads(mock_post.call_args.kwargs["data"])
    assert sent["seriesid"] == ["LASST480000000000003"]
    assert len(sent["seriesid"][0]) == 20
    assert result[0]["Status"] == "Success"


def test_bls_county_series_id_is_20_chars():
    from economic_research.tools import bls_api_skill

    with patch.object(
        bls_api_skill.requests, "post", return_value=_response(200, {})
    ) as mock_post:
        bls_api_skill.analyze_labor_force_quality("TX", county_fips="48453")
    sent = json.loads(mock_post.call_args.kwargs["data"])
    assert sent["seriesid"] == ["LAUCN484530000000003"]
    assert len(sent["seriesid"][0]) == 20


def test_bls_unknown_state_errors_instead_of_texas():
    from economic_research.tools import bls_api_skill

    with patch.object(bls_api_skill.requests, "post") as mock_post:
        result = json.loads(bls_api_skill.analyze_labor_force_quality("ZZ"))
    assert "Unknown state" in result["ERROR"]
    mock_post.assert_not_called()


def test_bls_missing_value_is_not_success():
    from economic_research.tools import bls_api_skill

    payload = {
        "Results": {
            "series": [
                {"seriesID": "A", "data": []},
                {
                    "seriesID": "B",
                    "data": [{"value": "-", "periodName": "May", "year": "1"}],
                },
            ]
        }
    }
    with patch.object(
        bls_api_skill.requests, "post", return_value=_response(200, payload)
    ):
        result = json.loads(bls_api_skill.fetch_bls_series_data(["A", "B"]))
    assert [r["Status"] for r in result] == ["No data", "No data"]
    assert all(r["Current Value"] == "N/A" for r in result)


def test_bls_error_does_not_leak_key(monkeypatch):
    from economic_research.tools import bls_api_skill

    monkeypatch.setenv("BLS_API_KEY", "BLSKEY000000")
    err = requests.ConnectionError("failed registrationkey=BLSKEY000000")
    with patch.object(bls_api_skill.requests, "post", side_effect=err):
        result = bls_api_skill.fetch_bls_series_data(["X"])
    assert "ConnectionError" in result
    assert "BLSKEY000000" not in result


# --- M6: econometrics ------------------------------------------------------


def test_adf_ignores_mismatched_independent_values():
    from economic_research.tools.econometrics_skill import (
        run_econometric_regression,
    )

    y = [1.0, 3.0, 2.0, 5.0, 4.0, 6.0, 5.0, 8.0, 7.0, 9.0, 8.0, 11.0]
    adf = json.loads(run_econometric_regression(y, [1.0, 2.0], None, "ADF"))
    assert adf["Analysis"] == "Augmented Dickey-Fuller (ADF) Stationarity Test"
    empty_x = json.loads(run_econometric_regression(y, [], None, "adf"))
    assert "ERROR" not in empty_x
    ols = json.loads(run_econometric_regression(y, [1.0, 2.0], None, "OLS"))
    assert "Dimension mismatch" in ols["ERROR"]


# --- M1 / M7: BEA ------------------------------------------------------------


def _bea_payload(entries):
    return {"BEAAPI": {"Results": {"Data": entries}}}


def test_bea_falls_back_to_latest_numeric_year_with_response_units(
    monkeypatch,
):
    from economic_research.tools import bea_skill

    monkeypatch.setenv("BEA_API_KEY", "bea-test-key")
    unit = {"CL_UNIT": "Thousands of chained 2017 dollars", "UNIT_MULT": "3"}
    entries = [
        {"TimePeriod": "2021", "DataValue": "1,000", **unit},
        {"TimePeriod": "2022", "DataValue": "1,234,567", **unit},
        {"TimePeriod": "2023", "DataValue": "(NA)", **unit},
    ]
    with patch.object(
        bea_skill.requests,
        "get",
        return_value=_response(200, _bea_payload(entries)),
    ) as mock_get:
        result = json.loads(bea_skill.fetch_bea_regional_data(["Austin"]))

    assert result[0]["Year"] == "2022"
    assert result[0]["Value"] == "$1,234,567"
    assert "Thousands of chained 2017 dollars" in result[0]["Metric"]
    assert "Millions" not in result[0]["Metric"]
    assert "2023" in result[0]["Note"]
    params = mock_get.call_args.kwargs["params"]
    assert (params["TableName"], params["LineCode"]) == ("CAGDP9", "1")


def test_bea_personal_income_uses_cainc1(monkeypatch):
    from economic_research.tools import bea_skill

    monkeypatch.setenv("BEA_API_KEY", "bea-test-key")
    entries = [
        {
            "TimePeriod": "2023",
            "DataValue": "250,000",
            "CL_UNIT": "Thousands of dollars",
            "UNIT_MULT": "3",
        }
    ]
    with patch.object(
        bea_skill.requests,
        "get",
        return_value=_response(200, _bea_payload(entries)),
    ) as mock_get:
        result = json.loads(
            bea_skill.fetch_bea_regional_data(["Raleigh"], "Personal Income")
        )
    params = mock_get.call_args.kwargs["params"]
    assert (params["TableName"], params["LineCode"]) == ("CAINC1", "1")
    assert result[0]["Metric"] == "Personal Income (Thousands of dollars)"


def test_bea_rejects_unsupported_report_type(monkeypatch):
    from economic_research.tools import bea_skill

    monkeypatch.setenv("BEA_API_KEY", "bea-test-key")
    with patch.object(bea_skill.requests, "get") as mock_get:
        result = json.loads(
            bea_skill.fetch_bea_regional_data(["Austin"], "Housing Starts")
        )
    assert "Unsupported report_type" in result["ERROR"]
    mock_get.assert_not_called()


def test_bea_error_does_not_leak_key(monkeypatch):
    from economic_research.tools import bea_skill

    monkeypatch.setenv("BEA_API_KEY", "BEASECRET12345")
    err = requests.ConnectionError(
        "GET https://apps.bea.gov/api/data?UserID=BEASECRET12345 failed"
    )
    with patch.object(bea_skill.requests, "get", side_effect=err):
        result = bea_skill.fetch_bea_regional_data(["Austin"])
    assert "ConnectionError" in result
    assert "BEASECRET12345" not in result


# --- M14: trade ----------------------------------------------------------------


def test_trade_maps_columns_by_header_and_latest_month(monkeypatch):
    from economic_research.tools import trade_skill

    monkeypatch.setenv("CENSUS_API_KEY", "census-test-key")
    data = [
        ["E_COMMODITY", "time", "ALL_VAL_YR", "STATE", "E_COMMODITY"],
        ["85", "2024-11", "40000000000", "TX", "85"],
        ["85", "2024-12", "45500000000", "TX", "85"],
        ["85", "2024-12", "900000000", "NC", "85"],
    ]
    with patch.object(
        trade_skill.requests, "get", return_value=_response(200, data)
    ) as mock_get:
        result = json.loads(
            trade_skill.fetch_regional_trade_data(
                ["Texas", "North Carolina", "Arizona"], "Semiconductors"
            )
        )
    by_state = {r["State"]: r for r in result}
    assert "$45.50B" in by_state["Texas"]["Market Profile"]
    assert "2024-12" in by_state["Texas"]["Market Profile"]
    assert "$900.00M" in by_state["North Carolina"]["Market Profile"]
    assert "Census" in by_state["Texas"]["Source"]
    # Arizona was not in the live response: sandbox, labelled.
    assert SANDBOX_SOURCE in by_state["Arizona"]["Source"]
    assert mock_get.call_args.kwargs["params"]["time"] == "2024-12"


def test_trade_sandbox_fallback_is_labelled():
    from economic_research.tools.trade_skill import fetch_regional_trade_data

    result = json.loads(fetch_regional_trade_data(["Texas"]))
    assert SANDBOX_SOURCE in result[0]["Source"]


# --- M5 / M11 / L7: MLS --------------------------------------------------------


def test_mls_sandbox_listings_are_labelled():
    from economic_research.tools import mls_property_analysis_skill as mls

    with (
        patch.object(
            mls,
            "fetch_hud_usps_crosswalk",
            return_value=json.dumps({"ERROR": "x"}),
        ),
        patch.object(
            mls, "fetch_hud_fmr_data", return_value=json.dumps({"ERROR": "x"})
        ),
    ):
        result = json.loads(
            mls.fetch_mls_property_listings("Columbus", property_type="condo")
        )
    assert result
    assert all(r["Source"] == SANDBOX_SOURCE for r in result)
    assert "default assumption" in result[0]["HUD FMR (2BR)"]


def test_mls_looks_up_fips_once_per_city_and_hides_key(caplog):
    from economic_research.tools import mls_property_analysis_skill as mls

    set_session_api_key("RENTCAST_API_KEY", "RENTSECRET12345")
    listings = [
        {
            "formattedAddress": f"{i} Main St",
            "price": 300000,
            "zipCode": "78702",
        }
        for i in range(3)
    ]
    crosswalk = MagicMock(return_value=json.dumps({"County_FIPS": "48453"}))
    fmr = MagicMock(
        return_value=json.dumps({"Rent_2BR": "$1,800", "Year": "2026"})
    )
    with (
        patch.object(
            mls.requests, "get", return_value=_response(200, listings)
        ) as mock_get,
        patch.object(mls, "fetch_hud_usps_crosswalk", crosswalk),
        patch.object(mls, "fetch_hud_fmr_data", fmr),
    ):
        result = json.loads(
            mls.fetch_mls_property_listings("Austin, TX", property_type="condo")
        )

    assert len(result) == 3
    assert crosswalk.call_count == 1
    assert fmr.call_count == 1
    assert all("RentCast" in r["Source"] for r in result)
    assert result[0]["HUD FMR (2BR)"] == "$1,800 (2026)"
    # The session key (not os.environ) is what gets sent.
    assert (
        mock_get.call_args.kwargs["headers"]["X-Api-Key"] == "RENTSECRET12345"
    )

    # A failing response body must not be logged (it may echo the key).
    caplog.set_level(logging.DEBUG)
    body = "invalid key RENTSECRET12345"
    with (
        patch.object(
            mls.requests, "get", return_value=_response(401, None, body)
        ),
        patch.object(mls, "fetch_hud_usps_crosswalk", crosswalk),
        patch.object(mls, "fetch_hud_fmr_data", fmr),
    ):
        fallback = json.loads(
            mls.fetch_mls_property_listings("Austin, TX", property_type="condo")
        )
    assert "RENTSECRET12345" not in caplog.text
    assert "401" in caplog.text
    assert all(r["Source"] == SANDBOX_SOURCE for r in fallback)


def test_mls_unresolved_city_uses_labelled_default_rent():
    from economic_research.tools import mls_property_analysis_skill as mls

    with patch.object(mls, "fetch_hud_fmr_data") as fmr:
        with patch(
            "economic_research.tools.dynamic_entity_resolver.resolve_fips",
            return_value="",
        ):
            with patch.object(
                mls,
                "fetch_hud_usps_crosswalk",
                return_value=json.dumps({"ERROR": "x"}),
            ):
                result = json.loads(
                    mls.fetch_mls_property_listings(
                        "Dallas", property_type="condo"
                    )
                )
    fmr.assert_not_called()  # no FMR lookup for an unresolved county
    assert "default assumption" in result[0]["HUD FMR (2BR)"]


# --- M10 / L5 / L9: static data labels -----------------------------------------


def test_labor_shift_static_and_default_are_labelled():
    from economic_research.tools.labor_shift_skill import model_labor_shifts

    data = json.loads(model_labor_shifts(["Austin", "Orlando"]))
    assert data[0]["Source"] == SANDBOX_SOURCE
    assert data[1]["Vulnerability Index (0-100)"] == 50
    assert "not a computed score" in data[1]["Score Type"]
    assert SANDBOX_SOURCE in data[1]["Source"]


def test_labor_shift_survives_fred_none_search():
    from economic_research.tools import labor_shift_skill

    fred = MagicMock()
    fred.search.return_value = None  # fredapi's "no results"
    fred.get_series.side_effect = ValueError("Bad Request. api_key=SECRET")
    with patch.object(labor_shift_skill, "get_fred_client", return_value=fred):
        data = json.loads(labor_shift_skill.model_labor_shifts(["Boise"]))
    assert data[0]["City"] == "Boise"
    assert "not a computed score" in data[0]["Score Type"]


def test_resolve_sector_series_handles_none_and_unrelated_hits():
    import pandas as pd

    from economic_research.tools.labor_shift_skill import resolve_sector_series

    fred = MagicMock()
    fred.search.return_value = None
    assert (
        resolve_sector_series(fred, "Boise", None, "Information", "info")
        is None
    )
    fred.search.return_value = pd.DataFrame(
        {"title": ["Unrelated series"]}, index=["XYZ"]
    )
    assert (
        resolve_sector_series(fred, "Boise", None, "Information", "info")
        is None
    )


def test_talent_pipeline_is_labelled_sandbox():
    from economic_research.tools.talent_pipeline_skill import (
        get_talent_pipeline_roi,
    )

    data = json.loads(get_talent_pipeline_roi(["Austin"], "Nursing"))
    assert SANDBOX_SOURCE in data[0]["Source"]
    assert "Grounded" not in data[0]["Source"]
    assert "Nursing" in data[0]["Note"]


def test_macro_foundation_is_labelled_sandbox(monkeypatch):
    from economic_research.tools.macro_foundation_skill import (
        get_state_macro_health,
    )

    monkeypatch.setenv("BEA_API_KEY", "bea-test-key")
    data = json.loads(get_state_macro_health(["Texas", "Ohio"]))
    assert all(d["Source"] == SANDBOX_SOURCE for d in data)


_TAX_HTML = """
<table>
  <tr><th>State</th><th>Rates</th><th>Brackets</th></tr>
  <tr><td>Alaska (a)</td><td>0%</td><td>&gt;$0</td></tr>
  <tr><td></td><td>9.4%</td><td>&gt;$222,000</td></tr>
  <tr><td>North Carolina</td><td>2.5%</td><td>&gt;$0</td></tr>
  <tr><td>Texas (b)</td><td>None</td><td></td></tr>
</table>
"""


def test_tax_foundation_case_insensitive_and_abbreviations():
    from economic_research.tools import tax_foundation_skill as tax

    with patch.object(
        tax.requests, "get", return_value=_response(200, None, _TAX_HTML)
    ):
        data = json.loads(tax.fetch_state_tax_rates(["texas", "NC", "Alaska"]))
    rates = {d["State"]: d["Corporate Tax Rate"] for d in data}
    assert rates == {"texas": "None", "NC": "2.5%", "Alaska": "0% / 9.4%"}
    assert all(d["Tax Year"] == "2024" for d in data)


def test_tax_foundation_structure_change_is_reported():
    from economic_research.tools import tax_foundation_skill as tax

    with patch.object(
        tax.requests,
        "get",
        return_value=_response(200, None, "<html>No tables</html>"),
    ):
        data = json.loads(tax.fetch_state_tax_rates(["Ohio", "Minnesota"]))
    assert all("structure changed" in d["Error"] for d in data)
    assert all(SANDBOX_SOURCE in d["Source"] for d in data)
    assert data[0]["Corporate Tax Rate"].startswith("None")


# --- H3 (inherited): metro matrix ---------------------------------------------


def test_metro_matrix_survives_fred_errors_and_unknown_state():
    from economic_research.tools import metro_matrix_skill as mm

    with (
        patch.object(
            mm,
            "fetch_regional_macro_stats",
            return_value="No FRED data found for the requested cities.",
        ),
        patch.object(
            mm,
            "get_state_macro_health",
            return_value=json.dumps([{"State": "Texas", "Source": "x"}]),
        ),
        patch.object(mm, "analyze_market_sentiment", return_value="[]"),
    ):
        data = json.loads(mm.generate_metro_matrix_report(["Austin", "Boise"]))

    assert data[0]["Macro Context"]["State"] == "Texas"
    # Boise's state is unknown: no Texas data borrowed for it.
    assert "State unknown" in data[1]["Macro Context"]["Message"]
    assert data[1]["Labor Context"]["Message"] == "No Labor Data"

    with (
        patch.object(
            mm, "fetch_regional_macro_stats", side_effect=AttributeError("x")
        ),
        patch.object(mm, "get_state_macro_health", return_value="ERROR: x"),
        patch.object(mm, "analyze_market_sentiment", return_value="[]"),
    ):
        data = json.loads(mm.generate_metro_matrix_report(["Austin"]))
    assert data[0]["Labor Context"]["Message"] == "No Labor Data"
