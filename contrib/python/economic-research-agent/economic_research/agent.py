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

"""
Economic Research Agent (ERA) - ADK 2.0 Implementation.
Replaces LangChain/LangGraph with native Vertex AI Agent Development Kit.
"""

import logging
import os
from collections.abc import Callable
from typing import Any

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools import ToolContext

from economic_research.audit_loop import (
    DRAFT_KEY,
    REVISIONS_KEY,
    VERDICT_KEY,
    AuditedResearchAgent,
)
from economic_research.shared_libraries.helper import (
    _SESSION_API_KEYS,
    KNOWN_API_KEYS,
    get_cloud_secret,
    get_default_model,
    get_session_api_key,
    init_session_api_keys,
    safe_error,
    set_session_api_key,
)
from economic_research.shared_libraries.tool_threads import run_all_in_threads

# Specialized Skill Imports
from economic_research.tools.bea_skill import fetch_bea_regional_data
from economic_research.tools.bls_skill import (
    labor_force_stats_skill,
    median_hourly_wages_skill,
    state_tax_rate_skill,
    state_union_employment_skill,
)
from economic_research.tools.census_skill import fetch_census_education_stats
from economic_research.tools.econometrics_skill import (
    run_econometric_regression,
)
from economic_research.tools.economic_index_skill import (
    fetch_anthropic_economic_index_data,
)
from economic_research.tools.eia_skill import fetch_state_electricity_rates
from economic_research.tools.fec_skill import (
    analyze_political_stability,
)
from economic_research.tools.fred_skill import fetch_regional_macro_stats
from economic_research.tools.hud_skill import (
    analyze_housing_affordability,
    fetch_hud_chas_data,
    fetch_hud_fmr_data,
    fetch_hud_income_limits,
    fetch_hud_usps_crosswalk,
)
from economic_research.tools.labor_shift_skill import (
    model_labor_shifts,
)
from economic_research.tools.macro_search_skill import (
    search_macro_series,
)
from economic_research.tools.mls_property_analysis_skill import (
    fetch_mls_property_listings,
)
from economic_research.tools.real_estate_skill import get_real_estate_roi
from economic_research.tools.regulatory_skill import fetch_regulatory_notices
from economic_research.tools.relocation_skill import (
    estimate_employee_relocation,
)
from economic_research.tools.scorecard_skill import (
    generate_location_scorecard,
)
from economic_research.tools.talent_pipeline_skill import (
    get_talent_pipeline_roi,
)
from economic_research.tools.tax_foundation_skill import fetch_state_tax_rates
from economic_research.tools.trade_skill import fetch_regional_trade_data
from economic_research.tools.underwriting_skill import (
    underwrite_deal_leverage,
)
from economic_research.tools.workforce_exposure_skill import (
    analyze_workforce_exposure,
)

from .prompt import Prompts

load_dotenv()
for _k, _v in list(os.environ.items()):
    if _v.startswith("<TODO:"):
        del os.environ[_k]

logger = logging.getLogger(__name__)

prompts = Prompts()
ERA_INSTRUCTIONS = prompts.main_era_instructions()

# Appended to the researcher's instructions when the Auditor Judge is active.
AUDIT_REVISION_NOTE = """

### Auditor Judge Revisions
An Auditor Judge reviews each report you write. If the most recent Auditor
Judge message in this conversation starts with [REJECT], use your tools to fix
every issue it lists and output the complete corrected report (not a diff).
"""


def _supervisor_bypassed() -> bool:
    """True when the Auditor Judge and router loops are disabled (e.g. CI)."""
    return os.getenv("ERA_BYPASS_SUPERVISOR", "").strip().lower() == "true"


def _event_text(event: Any) -> str:
    """Concatenates the text parts of an ADK event.

    Events can have ``content=None`` (state-only, errors, transfers) or parts
    without text (function calls), so neither may be dereferenced blindly.
    """
    return _content_text(getattr(event, "content", None))


def _content_text(content: Any) -> str:
    """Concatenates the text parts of a ``types.Content`` (None-safe)."""
    parts = getattr(content, "parts", None) if content else None
    if not parts:
        return ""
    return "".join(
        part.text
        for part in parts
        if isinstance(getattr(part, "text", None), str)
    )


def tool_error_to_result(
    tool: Any, args: dict[str, Any], tool_context: Any, error: Exception
) -> dict[str, str]:
    """ADK ``on_tool_error_callback``: turn a tool exception into a result.

    Without this, a single failing tool (bad input, API outage, malformed
    response) aborts the whole agent run. Only the exception type goes back to
    the model: exception messages from HTTP clients can embed request URLs
    that carry API keys.
    """
    tool_name = getattr(tool, "name", "unknown_tool")
    logger.warning(
        "Tool %s raised %s; returning error result to the model.",
        tool_name,
        type(error).__name__,
    )
    return {
        "ERROR": (
            f"Tool '{tool_name}' failed ({type(error).__name__}). Retry with "
            "different inputs or continue without this data source, and say "
            "that this data was unavailable."
        )
    }


def store_user_api_key(
    key_name: str, key_value: str, tool_context: ToolContext
) -> str:
    """Stores an API key that the user typed in this chat turn.

    Use this only when the user's own message contains the key (for example
    after you asked them for a missing FRED_API_KEY), then retry the failed
    operation.

    Args:
        key_name: The environment variable name, e.g. 'FRED_API_KEY'.
        key_value: The exact key value from the user's message.

    Returns:
        A confirmation or an error message.
    """
    # Prompt-injection guard: text returned by tools (web pages, API
    # responses) must not be able to swap in attacker-controlled keys, so the
    # value has to appear verbatim in the message the user sent this turn.
    user_text = _content_text(tool_context.user_content)
    if not key_value or key_value not in user_text:
        return (
            "ERROR: The key was not found in the user's latest message. Ask "
            "the user to paste the key directly in the chat."
        )
    return set_session_api_key(key_name, key_value)


def ensure_session_key_store(callback_context: Any) -> None:
    """``before_agent_callback``: create the per-invocation key store.

    Served paths (Agent Runtime, FastAPI, playground) never call
    ``init_session_api_keys()``. Creating the dict before tools run means a key
    stored by one tool call is visible to later calls in the same turn (tools
    run in worker threads with a copy of this context, and share the dict).
    """
    del callback_context
    if _SESSION_API_KEYS.get() is None:
        init_session_api_keys()


class ERAAgent:
    agent_framework = "google-adk"

    def __init__(self):
        """Standard container for the Reasoning Engine. State-free to ensure cloud pickling stability."""
        pass

    def get_app(self, model_name: str | None = None) -> App:
        """Lazily instantiates the ADK App and Agent only when needed.

        Unless ``ERA_BYPASS_SUPERVISOR=true``, the root agent is the audited
        research loop (researcher -> Auditor Judge -> optional revision).
        """
        resolved_model = get_default_model(
            model_name or os.getenv("MODEL_NAME")
        )
        tools: list[Callable[..., Any]] = [
            labor_force_stats_skill,
            median_hourly_wages_skill,
            state_tax_rate_skill,
            state_union_employment_skill,
            fetch_regional_macro_stats,
            fetch_state_electricity_rates,
            get_real_estate_roi,
            get_talent_pipeline_roi,
            fetch_census_education_stats,
            fetch_bea_regional_data,
            fetch_hud_fmr_data,
            fetch_hud_income_limits,
            analyze_housing_affordability,
            fetch_state_tax_rates,
            fetch_regional_trade_data,
            fetch_regulatory_notices,
            analyze_workforce_exposure,
            fetch_anthropic_economic_index_data,
            fetch_mls_property_listings,
            fetch_hud_usps_crosswalk,
            fetch_hud_chas_data,
            model_labor_shifts,
            analyze_political_stability,
            run_econometric_regression,
            underwrite_deal_leverage,
            generate_location_scorecard,
            estimate_employee_relocation,
            search_macro_series,
        ]
        # Blocking HTTP tools run in worker threads so one slow upstream API
        # doesn't stall every session on the event loop.
        tools = [*run_all_in_threads(tools), store_user_api_key]

        bypass = _supervisor_bypassed()
        era_agent = Agent(
            name="economic_research",
            model=Gemini(model=resolved_model),
            instruction=ERA_INSTRUCTIONS
            if bypass
            else ERA_INSTRUCTIONS + AUDIT_REVISION_NOTE,
            tools=tools,
            output_key=DRAFT_KEY,
            on_tool_error_callback=tool_error_to_result,
            before_agent_callback=ensure_session_key_store,
        )
        if bypass:
            return App(root_agent=era_agent, name="Economic_Research_Agent")

        from .sub_agents.agent import JudgeAgent

        audited_agent = AuditedResearchAgent(
            name="economic_research_audited",
            description=(
                "Economic research agent whose reports are fact-checked by an "
                "Auditor Judge and revised once on rejection."
            ),
            researcher=era_agent,
            judge=JudgeAgent().get_agent(output_key=VERDICT_KEY),
            max_revisions=1,
        )
        return App(root_agent=audited_agent, name="Economic_Research_Agent")

    def query(self, input: str) -> str:
        """Standard Reasoning Engine entry point (synchronous).

        Safe to call from code that already runs an event loop (FastAPI,
        Jupyter, async runtimes): ``asyncio.run`` would raise there, so the
        query runs on a fresh loop in a worker thread instead.
        """
        import asyncio

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self._query_async(input))

        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, self._query_async(input)).result()

    async def aquery(self, input: str) -> str:
        """Async entry point for callers that already have an event loop."""
        return await self._query_async(input)

    async def _run_app(
        self, app: App, text: str, user_id: str = "default_user"
    ) -> tuple[str, dict[str, Any]]:
        """Runs ``app`` once on ``text``.

        Returns:
            The concatenated text of all events and the final session state.
        """
        from google.adk.runners import InMemoryRunner
        from google.genai import types

        session_id = f"{user_id}_session"
        runner = InMemoryRunner(app=app)
        runner.auto_create_session = True

        full_text = ""
        async for event in runner.run_async(
            new_message=types.Content(
                role="user", parts=[types.Part.from_text(text=text)]
            ),
            user_id=user_id,
            session_id=session_id,
        ):
            full_text += _event_text(event)

        state: dict[str, Any] = {}
        try:
            session = await runner.session_service.get_session(
                app_name=app.name, user_id=user_id, session_id=session_id
            )
            if session is not None:
                state = dict(session.state)
        except Exception as exc:  # state is best-effort
            logger.debug("Could not read session state: %s", exc)
        return full_text, state

    async def _query_async(self, input: str) -> str:
        # Security Fix: Extract and mask API keys in input to prevent logging
        import re

        init_session_api_keys()
        modified_input = input
        for key in KNOWN_API_KEYS:
            pattern = f"{key}=([^\\s]+)"
            match = re.search(pattern, input)
            if match:
                set_session_api_key(key, match.group(1))
                # Mask it in the input string
                modified_input = re.sub(
                    pattern, f"{key}=**********", modified_input
                )
                logger.info(
                    "Masked %s in input and set it for the session.", key
                )

        # Cloud Secrets fallback using Secret Manager (cached per process).
        for key_name in KNOWN_API_KEYS:
            if get_session_api_key(key_name):
                continue
            secret_val = get_cloud_secret(key_name)
            if secret_val:
                set_session_api_key(key_name, secret_val)

        # Classify complexity of input query
        model_name = get_default_model(os.getenv("MODEL_NAME"))
        # Check if we should bypass supervisor & judge loops (e.g. to save API quota/rate limits)
        bypass_loops = _supervisor_bypassed()

        if not bypass_loops:
            try:
                import json

                router_model = get_default_model(os.getenv("MODEL_NAME"))
                classifier_agent = Agent(
                    name="router_supervisor",
                    model=Gemini(model=router_model),
                    instruction=prompts.complexity_classifier_instructions(),
                )
                classifier_text, _ = await self._run_app(
                    App(root_agent=classifier_agent, name="Router_Supervisor"),
                    modified_input,
                    user_id="classifier_user",
                )
                cleaned_text = (
                    classifier_text.replace("```json", "")
                    .replace("```", "")
                    .strip()
                )
                data = json.loads(cleaned_text)
                complexity = data.get("complexity", "LOW")
                if complexity == "HIGH":
                    model_name = get_default_model(
                        os.getenv("MODEL_NAME_GENERATED_1")
                    )
                    logger.info(
                        "[Router] High complexity task; routing to %s.",
                        model_name,
                    )
                else:
                    logger.info(
                        "[Router] Low complexity task; routing to %s.",
                        model_name,
                    )
            except Exception as e:
                logger.warning(
                    "[Router] Routing failed (%s); falling back to %s.",
                    safe_error(e),
                    model_name,
                )

        # Instantiate App & Runner at runtime rather than deploy-time.
        # Unless bypassed, the app's root agent already runs the Auditor Judge
        # loop (see economic_research/audit_loop.py).
        try:
            full_text, state = await self._run_app(
                self.get_app(model_name=model_name), modified_input
            )
        except Exception as e:
            if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
                fallback_model = get_default_model(os.getenv("MODEL_NAME"))
                logger.warning(
                    "[Quota] %s exhausted; falling back to %s.",
                    model_name,
                    fallback_model,
                )
                full_text, state = await self._run_app(
                    self.get_app(model_name=fallback_model), modified_input
                )
            else:
                raise

        # ⚖️ Compose the final report from the audited loop's session state.
        draft = state.get(DRAFT_KEY) or full_text
        verdict = state.get(VERDICT_KEY)
        if verdict:
            label = (
                "Self-Corrected v2" if state.get(REVISIONS_KEY) else "Passed v1"
            )
            final_report = (
                f"{draft}\n\n---\n### ⚖️ Auditor Judge Verification "
                f"({label})\n{verdict}"
            )
        else:
            final_report = draft

        # Calculate Economic Primitives of the completed session
        if not bypass_loops:
            try:
                import json

                eval_model = get_default_model(os.getenv("MODEL_NAME"))
                evaluator_agent = Agent(
                    name="primitives_evaluator",
                    model=Gemini(model=eval_model),
                    instruction="""
                    You are an economic operations analyst. Evaluate the completed interaction between the user and the economic research agent.
                    
                    Compute the following primitives:
                    1. "interaction_type": Classify into: directive, feedback_loop, task_iteration, validation, or learning.
                    2. "autonomy_level": Integer from 1 (active collaboration / human-in-the-loop) to 5 (fully autonomous delegation).
                    3. "human_only_time_minutes": Estimated time (in minutes) an experienced economic analyst would spend to complete this task manually (e.g., searching FRED/BLS, scraping tax rates, drafting tables, and writing reports).
                    4. "human_education_years_required": Estimated years of education/training needed to understand this request (e.g., 12 for high school, 16 for college, 18+ for grad school/PhD).
                    5. "task_success": Boolean (true/false) indicating if the agent successfully fulfilled the user request with accurate data.
                    
                    Output your evaluation as a valid JSON object. Do not include markdown formatting or additional explanation.
                    """,
                )
                evaluation_prompt = f"### User Query:\n{modified_input}\n\n### Agent Final Response:\n{final_report}"
                eval_text, _ = await self._run_app(
                    App(
                        root_agent=evaluator_agent, name="Primitives_Evaluator"
                    ),
                    evaluation_prompt,
                    user_id="evaluator_user",
                )

                # Save or log the metrics
                cleaned_eval = (
                    eval_text.replace("```json", "").replace("```", "").strip()
                )
                primitives = json.loads(cleaned_eval)

                import tempfile

                raw_log_dir = os.getenv("OBSERVABILITY_LOG_DIR")
                log_dir = (
                    raw_log_dir
                    if raw_log_dir and not raw_log_dir.startswith("<TODO:")
                    else os.path.join(tempfile.gettempdir(), "observability")
                )
                os.makedirs(log_dir, exist_ok=True)
                import uuid

                session_id = str(uuid.uuid4())
                log_path = os.path.join(log_dir, f"{session_id}.json")
                with open(log_path, "w") as f:
                    json.dump(
                        {
                            "session_id": session_id,
                            "query": modified_input,
                            "primitives": primitives,
                        },
                        f,
                        indent=2,
                    )

                logger.info(
                    "[Observability] Logged economic primitives to %s: %s",
                    log_path,
                    primitives,
                )
            except Exception as e:
                logger.warning(
                    "[Observability] Failed to evaluate economic primitives: %s",
                    safe_error(e),
                )

        return final_report

    def generate_whitepaper(self, research_topic: str) -> str:
        """
        Generates a premium Corporate Whitepaper autonomously for ANY 'Wow Factor' topic.
        """
        from economic_research.orchestrators.universal_whitepaper_orchestrator import (
            solve as universal_solve,
        )

        eval_inputs = {"research_topic": research_topic}
        return universal_solve(eval_inputs)

    def generate_real_estate_brief(
        self,
        city_names: list[str],
        property_type: str = "single-family",
        mortgage_rate: float = 0.068,
        down_payment_pct: float = 0.20,
    ) -> str:
        """
        Generates a pro-forma Real Estate Portfolio & Yield Investment Brief.
        """
        from economic_research.advisors.real_estate_advisor import (
            RealEstatePortfolioAdvisor,
        )

        advisor = RealEstatePortfolioAdvisor(
            mortgage_rate=mortgage_rate, down_payment_pct=down_payment_pct
        )
        return advisor.generate_investment_brief(
            city_names=city_names, property_type=property_type
        )


export_agent = ERAAgent()

# Also export root_agent for local CLI usage
root_agent = export_agent.get_app().root_agent

# Export the App as 'agent' for run_eval.py
agent = export_agent.get_app()


def main() -> None:
    """Interactive terminal session (used by `make run`)."""
    print("🧠 Economic Research Agent. Type 'exit' or press Ctrl-D to quit.")
    while True:
        try:
            question = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not question:
            continue
        if question.lower() in {"exit", "quit"}:
            break
        print(f"\nERA:\n{export_agent.query(question)}")


if __name__ == "__main__":
    main()
