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

"""Regression tests for tool failure modes that used to abort agent runs.

Every tool result must be JSON-serializable and must not raise on missing
keys, empty API responses or malformed inputs.
"""

import asyncio
import json
from collections.abc import AsyncGenerator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.events import Event
from google.adk.models import BaseLlm, LlmRequest, LlmResponse
from google.adk.runners import InMemoryRunner
from google.genai import types

from economic_research.shared_libraries import helper
from economic_research.shared_libraries.helper import init_session_api_keys


@pytest.fixture(autouse=True)
def fresh_session_keys():
    """Session API keys live in a ContextVar; isolate each test."""
    init_session_api_keys()
    yield
    init_session_api_keys()


# --- Deploy blocker: model resolution --------------------------------------


def test_default_model_without_env_or_env_example(monkeypatch):
    """Containers ship neither .env nor .env.example; model must not be ''."""
    monkeypatch.delenv("MODEL_NAME", raising=False)
    monkeypatch.setattr(
        helper, "_ENV_EXAMPLE_PATH", Path("/nonexistent/.env.example")
    )
    assert helper.get_default_model() == helper.DEFAULT_MODEL
    assert helper.DEFAULT_MODEL == "gemini-3.5-flash"


def test_default_model_ignores_placeholder(monkeypatch):
    monkeypatch.setenv("MODEL_NAME", "<TODO: update-this-value>")
    monkeypatch.setattr(
        helper, "_ENV_EXAMPLE_PATH", Path("/nonexistent/.env.example")
    )
    assert helper.get_default_model() == helper.DEFAULT_MODEL


# --- H1 / H2: BLS wrappers over FRED -----------------------------------------


def test_labor_force_stats_error_path_is_json_serializable():
    from economic_research.tools.bls_skill import labor_force_stats_skill

    with patch(
        "economic_research.tools.fred_skill.fetch_regional_macro_stats",
        return_value="ERROR: FRED_API_KEY is not set in environment variables.",
    ):
        result = labor_force_stats_skill(["Austin"])

    json.dumps(result)  # used to fail: DataFrame is not JSON serializable
    assert "FRED_API_KEY" in result[0][0]["Message"]


@pytest.mark.parametrize(
    "skill_name, arg",
    [
        ("median_hourly_wages_skill", ["Austin"]),
        ("state_union_employment_skill", ["Texas"]),
    ],
)
def test_fred_skills_without_key_return_error(monkeypatch, skill_name, arg):
    from economic_research.tools import bls_skill

    monkeypatch.delenv("FRED_API_KEY", raising=False)
    result = getattr(bls_skill, skill_name)(arg)  # used to raise ValueError

    json.dumps(result)
    assert "FRED_API_KEY" in result[0][0]["ERROR"]


@pytest.mark.parametrize(
    "skill_name, arg",
    [
        ("median_hourly_wages_skill", ["Austin"]),
        ("state_union_employment_skill", ["Texas"]),
    ],
)
def test_fred_skills_survive_api_failures(monkeypatch, skill_name, arg):
    from economic_research.tools import bls_skill

    monkeypatch.setenv("FRED_API_KEY", "mock_key")
    with patch("economic_research.tools.bls_functions.Fred") as mock_fred:
        mock_fred.return_value.search.side_effect = RuntimeError("503")
        result = getattr(bls_skill, skill_name)(arg)

    json.dumps(result)
    assert "No " in result[0][0]["Message"]


# --- H3 / M9: FRED regional macro stats -------------------------------------


def test_fred_unmapped_city_with_empty_search_does_not_raise(monkeypatch):
    from economic_research.tools.fred_skill import fetch_regional_macro_stats

    monkeypatch.setenv("FRED_API_KEY", "mock_key")
    with patch("economic_research.tools.fred_skill.Fred") as mock_fred:
        # fredapi returns None (not an empty DataFrame) for empty searches.
        mock_fred.return_value.search.return_value = None
        result = fetch_regional_macro_stats(["Boise, ID"])

    assert result.startswith("No FRED data found")


def test_fred_search_hit_is_used_as_full_series_id(monkeypatch):
    from economic_research.tools.fred_skill import fetch_regional_macro_stats

    monkeypatch.setenv("FRED_API_KEY", "mock_key")
    dates = pd.date_range("2020-01-01", periods=4, freq="YS")
    series = pd.Series([3.1, 3.2, 3.3, float("nan")], index=dates)
    with patch("economic_research.tools.fred_skill.Fred") as mock_fred:
        client = mock_fred.return_value
        client.search.return_value = pd.DataFrame(
            {"id": ["BOIS716UR"]}, index=["BOIS716UR"]
        )
        client.get_series.return_value = series
        result = json.loads(fetch_regional_macro_stats(["Boise"]))

    # Used to append the suffix again and request "BOIS716URUR".
    client.get_series.assert_called_once_with("BOIS716UR")
    # Trailing FRED '.' (NaN) observations are dropped, not shown as "nan%".
    assert result[0]["Latest Value"] == "3.30%"
    assert result[0]["Source"] == "FRED (BOIS716UR)"


# --- H4: HUD CHAS ------------------------------------------------------------


def test_hud_chas_rejects_non_numeric_fips(monkeypatch):
    from economic_research.tools.hud_skill import fetch_hud_chas_data

    monkeypatch.setenv("HUD_API_KEY", "mock_key")
    with patch("economic_research.tools.hud_skill.requests.get") as mock_get:
        result = json.loads(fetch_hud_chas_data("Tulsa"))  # used to raise

    assert "Invalid 5-digit County FIPS" in result["ERROR"]
    mock_get.assert_not_called()


# --- M3: scorecard weights ---------------------------------------------------


def test_scorecard_accepts_partial_weights():
    from economic_research.tools import scorecard_skill

    tax = json.dumps([{"Corporate Tax Rate": "5.0%"}])
    with (
        patch.object(
            scorecard_skill, "fetch_state_tax_rates", return_value=tax
        ),
        patch.object(
            scorecard_skill, "fetch_state_electricity_rates", return_value="[]"
        ),
        patch.object(
            scorecard_skill, "analyze_labor_force_quality", return_value="{}"
        ),
    ):
        result = json.loads(
            scorecard_skill.generate_location_scorecard(
                ["TX", "OH"], weights={"corporate_tax": 1}
            )
        )

    assert "ERROR" not in result
    assert result["Criteria_Weights"] == {
        "corporate_tax": "100.0%",
        "electricity_rate": "0.0%",
        "labor_quality_index": "0.0%",
    }


# --- M4: MLS listings --------------------------------------------------------


def test_mls_skips_listings_without_valid_price(monkeypatch):
    from economic_research.tools import mls_property_analysis_skill as mls

    monkeypatch.setenv("RENTCAST_API_KEY", "mock_key")
    listings = [
        {"formattedAddress": "1 No Price St", "price": None, "zipCode": None},
        {"formattedAddress": "2 Zero St", "price": 0, "zipCode": None},
        {
            "formattedAddress": "3 Good St",
            "price": 300000,
            "bedrooms": "3",  # non-numeric beds must not raise
            "zipCode": None,
        },
    ]
    response = MagicMock(status_code=200)
    response.json.return_value = listings
    fmr = json.dumps({"Rent_2BR": "$1,500", "Year": "2026"})
    with (
        patch.object(mls.requests, "get", return_value=response),
        patch.object(mls, "fetch_hud_fmr_data", return_value=fmr),
        patch(
            "economic_research.tools.dynamic_entity_resolver.resolve_fips",
            return_value="48453",
        ),
    ):
        result = json.loads(
            mls.fetch_mls_property_listings("Austin, TX", property_type="condo")
        )

    assert [r["Address"] for r in result] == ["3 Good St"]
    assert result[0]["Estimated Cap Rate"].endswith("%")


# --- M13: Federal Register ---------------------------------------------------


def test_regulatory_notices_isolate_failures_and_encode_topic():
    from economic_research.tools import regulatory_skill

    ok = MagicMock(status_code=200)
    ok.json.return_value = {
        "results": [{"title": "Rule", "agency_names": []}]  # empty list
    }
    with patch.object(
        regulatory_skill.requests,
        "get",
        side_effect=[requests.ConnectionError("url?key=secret"), ok],
    ) as mock_get:
        result = json.loads(
            regulatory_skill.fetch_regulatory_notices(
                ["Texas", "Ohio"], industry_topic="Oil & Gas"
            )
        )

    # One state failing no longer discards the other state's results.
    assert result[0]["State"] == "Texas"
    assert "ConnectionError" in result[0]["ERROR"]
    assert "secret" not in result[0]["ERROR"]
    assert result[1]["Notices"][0]["Agency"] == "N/A"
    # The topic is passed as a param (URL-encoded), not spliced into the URL.
    _, kwargs = mock_get.call_args
    assert kwargs["params"]["conditions[term]"] == "Ohio Oil & Gas"


# --- A3: event text extraction -----------------------------------------------


def test_event_text_handles_missing_content_and_non_text_parts():
    from economic_research.agent import _event_text

    assert _event_text(Event(author="x")) == ""  # content is None
    call_only = Event(
        author="x",
        content=types.Content(
            role="model",
            parts=[types.Part(function_call=types.FunctionCall(name="f"))],
        ),
    )
    assert _event_text(call_only) == ""
    mixed = Event(
        author="x",
        content=types.Content(
            role="model", parts=[types.Part(text="a"), types.Part(text="b")]
        ),
    )
    assert _event_text(mixed) == "ab"


# --- Tool-error safety net ---------------------------------------------------


class _ScriptedLlm(BaseLlm):
    """Returns canned responses in order; no network."""

    responses: list[LlmResponse]

    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncGenerator[LlmResponse, None]:
        yield self.responses.pop(0)


@pytest.mark.parametrize("threaded", [False, True])
def test_tool_exception_becomes_error_result_not_run_failure(threaded):
    """Also covers tools wrapped by ``run_in_thread`` (as in ``get_app``)."""
    from economic_research.agent import tool_error_to_result
    from economic_research.shared_libraries.tool_threads import run_in_thread

    def exploding_tool(city: str) -> dict:
        """Always fails, like a tool hitting a malformed API response."""
        raise ValueError(f"GET https://api.example?api_key=SECRET for {city}")

    llm = _ScriptedLlm(
        model="scripted",
        responses=[
            LlmResponse(
                content=types.Content(
                    role="model",
                    parts=[
                        types.Part(
                            function_call=types.FunctionCall(
                                name="exploding_tool", args={"city": "Tulsa"}
                            )
                        )
                    ],
                )
            ),
            LlmResponse(
                content=types.Content(
                    role="model", parts=[types.Part(text="Data unavailable.")]
                )
            ),
        ],
    )
    agent = Agent(
        name="t",
        model=llm,
        tools=[run_in_thread(exploding_tool) if threaded else exploding_tool],
        on_tool_error_callback=tool_error_to_result,
    )

    async def _go() -> list[Event]:
        runner = InMemoryRunner(app=App(root_agent=agent, name="tool_err"))
        session = await runner.session_service.create_session(
            app_name="tool_err", user_id="u"
        )
        return [
            e
            async for e in runner.run_async(
                user_id="u",
                session_id=session.id,
                new_message=types.Content(
                    role="user", parts=[types.Part(text="go")]
                ),
            )
        ]

    events = asyncio.run(_go())  # used to raise ValueError out of the run

    responses = [
        part.function_response.response
        for e in events
        if e.content and e.content.parts
        for part in e.content.parts
        if part.function_response
    ]
    assert len(responses) == 1
    assert "ValueError" in responses[0]["ERROR"]
    assert "SECRET" not in json.dumps(responses)  # no key leakage
    assert events[-1].content.parts[0].text == "Data unavailable."
