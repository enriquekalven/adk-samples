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

"""Agent-level hardening: key handling, timeouts, threads, event loops."""

import asyncio
import contextvars
import inspect
import json
import threading
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from google.adk.tools import FunctionTool
from google.genai import types

from economic_research.agent import (
    ERAAgent,
    ensure_session_key_store,
    store_user_api_key,
)
from economic_research.shared_libraries import helper
from economic_research.shared_libraries.fred_client import TimeoutFred
from economic_research.shared_libraries.helper import (
    _SESSION_API_KEYS,
    KNOWN_API_KEYS,
    get_session_api_key,
    init_session_api_keys,
    redact_secrets,
    safe_error,
    set_session_api_key,
)
from economic_research.shared_libraries.tool_threads import run_in_thread


@pytest.fixture
def fresh_context():
    """Runs the test body's key-store mutations in an isolated context."""
    token = _SESSION_API_KEYS.set(None)
    yield
    _SESSION_API_KEYS.reset(token)


# --- Key redaction (M1) ---------------------------------------------------


def test_redact_secrets_removes_query_param_keys():
    text = (
        "HTTPSConnectionPool: /data?api_key=abc123SECRET&year=2024 "
        "and ?registrationkey=XYZ987&UserID=zz"
    )
    redacted = redact_secrets(text)
    assert "abc123SECRET" not in redacted
    assert "XYZ987" not in redacted
    assert "api_key=REDACTED" in redacted
    assert "year=2024" in redacted


def test_safe_error_redacts_known_key_values(monkeypatch):
    monkeypatch.setenv("BEA_API_KEY", "BEAKEY-7777")
    err = ConnectionError("failed for https://x/?UserID=BEAKEY-7777 path")
    message = safe_error(err)
    assert message.startswith("ConnectionError: ")
    assert "BEAKEY-7777" not in message


def test_safe_error_truncates_long_messages():
    assert len(safe_error(ValueError("x" * 1000))) < 260


# --- Key registry (A8 / M11) ----------------------------------------------


@pytest.mark.parametrize("key_name", ["RENTCAST_API_KEY", "ONET_API_KEY"])
def test_rentcast_and_onet_keys_are_settable(fresh_context, key_name):
    init_session_api_keys()
    assert "Successfully set" in set_session_api_key(key_name, "k-123456")
    assert get_session_api_key(key_name) == "k-123456"


def _tool_context(user_text: str | None) -> SimpleNamespace:
    content = (
        types.Content(role="user", parts=[types.Part.from_text(text=user_text)])
        if user_text is not None
        else None
    )
    return SimpleNamespace(user_content=content)


def test_store_user_api_key_accepts_key_from_user_message(fresh_context):
    init_session_api_keys()
    ctx = _tool_context("here you go FRED_API_KEY=fredvalue123")
    result = store_user_api_key("FRED_API_KEY", "fredvalue123", ctx)
    assert "Successfully set" in result
    assert get_session_api_key("FRED_API_KEY") == "fredvalue123"


def test_store_user_api_key_rejects_injected_key(fresh_context, monkeypatch):
    """A key that only appears in tool output (prompt injection) is refused."""
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    init_session_api_keys()
    ctx = _tool_context("compare Austin and Denver unemployment")
    result = store_user_api_key("FRED_API_KEY", "attacker-key", ctx)
    assert result.startswith("ERROR")
    assert get_session_api_key("FRED_API_KEY") is None


def test_store_user_api_key_handles_missing_user_content(fresh_context):
    result = store_user_api_key("FRED_API_KEY", "v", _tool_context(None))
    assert result.startswith("ERROR")


def test_ensure_session_key_store_initializes_once(fresh_context):
    assert _SESSION_API_KEYS.get() is None
    ensure_session_key_store(None)
    store = _SESSION_API_KEYS.get()
    assert store == {}
    store["FRED_API_KEY"] = "kept"
    ensure_session_key_store(None)  # must not wipe keys set earlier
    assert _SESSION_API_KEYS.get() == {"FRED_API_KEY": "kept"}


def test_set_session_api_key_is_not_an_llm_tool():
    app = ERAAgent().get_app()
    researcher = getattr(app.root_agent, "researcher", app.root_agent)
    names = {
        getattr(t, "__name__", getattr(t, "name", "")) for t in researcher.tools
    }
    assert "set_session_api_key" not in names
    assert "store_user_api_key" in names


# --- Tools run off the event loop (M12) -----------------------------------


def test_root_tools_are_async_and_schema_is_unchanged():
    app = ERAAgent().get_app()
    researcher = getattr(app.root_agent, "researcher", app.root_agent)
    for tool in researcher.tools:
        if tool is store_user_api_key:
            continue
        assert inspect.iscoroutinefunction(tool), tool.__name__
        original = tool.__wrapped__
        assert (
            FunctionTool(tool)._get_declaration()
            == FunctionTool(original)._get_declaration()
        ), tool.__name__


def test_run_in_thread_runs_off_loop_thread_and_keeps_context(fresh_context):
    init_session_api_keys()
    set_session_api_key("FRED_API_KEY", "ctx-key-123")

    def blocking_tool(city: str) -> dict:
        return {
            "thread": threading.get_ident(),
            "key": get_session_api_key("FRED_API_KEY"),
            "city": city,
        }

    async def main():
        result = await run_in_thread(blocking_tool)(city="Austin")
        return threading.get_ident(), result

    loop_thread, result = asyncio.run(main())
    assert result["thread"] != loop_thread
    assert result["key"] == "ctx-key-123"
    assert result["city"] == "Austin"


def test_run_in_thread_leaves_async_functions_alone():
    async def already_async():
        return 1

    assert run_in_thread(already_async) is already_async


# --- query() inside a running event loop (A4) -----------------------------


def test_query_works_inside_running_event_loop():
    agent = ERAAgent()

    async def fake_query_async(text):
        return f"report for {text}"

    async def caller():
        return agent.query("Austin")

    with patch.object(agent, "_query_async", side_effect=fake_query_async):
        assert asyncio.run(caller()) == "report for Austin"
        assert agent.query("Denver") == "report for Denver"


def test_aquery_awaits_query_async():
    agent = ERAAgent()

    async def fake_query_async(text):
        return text.upper()

    with patch.object(agent, "_query_async", side_effect=fake_query_async):
        assert asyncio.run(agent.aquery("ok")) == "OK"


# --- Secret Manager lookups are cached (A6) -------------------------------


def test_get_cloud_secret_caches_hits_and_misses(monkeypatch, fresh_context):
    for key in KNOWN_API_KEYS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(helper, "_SECRET_CACHE", {})
    monkeypatch.setattr(helper, "_default_project_id", lambda: "proj")
    calls = []

    def fake_access(project_id, secret_id, **_):
        calls.append(secret_id)
        if secret_id == "FRED_API_KEY":
            return "fred-secret"
        raise RuntimeError("NotFound")

    monkeypatch.setattr(helper, "access_secret_version", fake_access)
    assert helper.get_cloud_secret("FRED_API_KEY") == "fred-secret"
    assert helper.get_cloud_secret("FRED_API_KEY") == "fred-secret"
    assert helper.get_cloud_secret("BEA_API_KEY") is None
    assert helper.get_cloud_secret("BEA_API_KEY") is None
    assert calls == ["FRED_API_KEY", "BEA_API_KEY"]


def test_get_cloud_secret_skips_lookup_without_project(
    monkeypatch, fresh_context
):
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    monkeypatch.setattr(helper, "_default_project_id", lambda: None)
    access = MagicMock()
    monkeypatch.setattr(helper, "access_secret_version", access)
    assert helper.get_cloud_secret("FRED_API_KEY") is None
    access.assert_not_called()


def test_get_cloud_secret_prefers_env(monkeypatch, fresh_context):
    monkeypatch.setenv("FRED_API_KEY", "from-env")
    access = MagicMock()
    monkeypatch.setattr(helper, "access_secret_version", access)
    assert helper.get_cloud_secret("FRED_API_KEY") == "from-env"
    access.assert_not_called()


# --- FRED requests time out (H5) ------------------------------------------

_SERIES_XML = b"""<?xml version="1.0" encoding="utf-8"?>
<observations realtime_start="2024-01-01" realtime_end="2024-01-01"
  observation_start="2024-01-01" observation_end="2024-02-01" units="lin"
  output_type="1" file_type="xml" order_by="observation_date"
  sort_order="asc" count="2" offset="0" limit="100000">
  <observation realtime_start="2024-01-01" realtime_end="2024-01-01"
    date="2024-01-01" value="3.4"/>
  <observation realtime_start="2024-01-01" realtime_end="2024-01-01"
    date="2024-02-01" value="3.6"/>
</observations>"""


def test_timeout_fred_passes_timeout_and_parses(monkeypatch):
    captured = {}

    def fake_get(url, params=None, timeout=None):
        captured.update(url=url, params=params, timeout=timeout)
        return SimpleNamespace(status_code=200, content=_SERIES_XML)

    monkeypatch.setattr(
        "economic_research.shared_libraries.fred_client.requests.get",
        fake_get,
    )
    fred = TimeoutFred(api_key="fredkey", timeout=3)
    series = fred.get_series("AUST448UR")
    assert captured["timeout"] == 3
    assert captured["params"] == {"api_key": "fredkey"}
    assert "fredkey" not in captured["url"]
    assert list(series.values) == [3.4, 3.6]


def test_timeout_fred_error_does_not_leak_key(monkeypatch):
    body = b'<error code="400" message="Bad Request.  Series does not exist."/>'
    monkeypatch.setattr(
        "economic_research.shared_libraries.fred_client.requests.get",
        lambda *a, **k: SimpleNamespace(status_code=400, content=body),
    )
    with pytest.raises(ValueError) as exc_info:
        TimeoutFred(api_key="fredkey").get_series("NOPE")
    assert "Series does not exist" in str(exc_info.value)
    assert "fredkey" not in str(exc_info.value)


def test_context_copy_shares_key_store(fresh_context):
    """Worker threads get a context copy; the shared dict keeps keys visible."""
    init_session_api_keys()
    ctx = contextvars.copy_context()
    ctx.run(set_session_api_key, "HUD_API_KEY", "hud-123456")
    assert get_session_api_key("HUD_API_KEY") == "hud-123456"


# --- Advisor / utility skill: no fabricated values -------------------------


def test_advisor_skips_listing_without_price():
    from economic_research.advisors.real_estate_advisor import (
        RealEstatePortfolioAdvisor,
    )

    advisor = RealEstatePortfolioAdvisor()
    assert advisor.calculate_investment_yield({"Price": "N/A"}, 1500.0) is None
    assert advisor.calculate_investment_yield({"Price": "$0"}, 1500.0) is None
    row = advisor.calculate_investment_yield(
        {"Price": "$250,000", "Beds/Baths": "2B/1Ba"}, 1500.0
    )
    assert row["Price"] == "$250,000"
    assert "Rent Basis" in row


def test_advisor_labels_default_rent_and_uses_3_person_ami(monkeypatch):
    import economic_research.advisors.real_estate_advisor as adv

    listings = [{"Price": "$200,000", "Beds/Baths": "2B/1Ba", "Source": "X"}]
    monkeypatch.setattr(
        adv, "fetch_mls_property_listings", lambda **_: json.dumps(listings)
    )
    seen = {}

    def fake_income(fips, household_size=1):
        seen["household_size"] = household_size
        return json.dumps({"AMI_50_Level": "$40,000"})

    monkeypatch.setattr(adv, "resolve_fips", lambda name: "48453")
    monkeypatch.setattr(adv, "fetch_hud_fmr_data", lambda f: "not json")
    monkeypatch.setattr(adv, "fetch_hud_income_limits", fake_income)
    rows = adv.RealEstatePortfolioAdvisor().evaluate_city("Austin, TX")
    assert seen["household_size"] == 3
    assert rows[0]["Rent Basis"].startswith(helper.SANDBOX_SOURCE)
    assert rows[0]["Listing Source"] == "X"


def test_utility_skill_labels_fallback_as_sandbox(monkeypatch):
    import economic_research.tools.eia_skill as eia
    from economic_research.tools.utility_logistics_skill import (
        get_industrial_infrastructure_stats,
    )

    monkeypatch.setattr(
        eia,
        "fetch_state_electricity_rates",
        lambda codes, sector="industrial": json.dumps(
            [{"State": codes[0], "Avg Price (cents/kWh)": "N/A"}]
        ),
    )
    rows = json.loads(get_industrial_infrastructure_stats(["Texas"]))
    assert rows[0]["Source"].startswith(helper.SANDBOX_SOURCE)
