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

"""Unit tests for the audited research loop (researcher -> judge -> revise)."""

import asyncio
from collections.abc import AsyncGenerator
from typing import Any

from google.adk.agents import BaseAgent, LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.apps import App
from google.adk.events import Event, EventActions
from google.adk.runners import InMemoryRunner
from google.genai import types

from economic_research.audit_loop import (
    DRAFT_KEY,
    REVISIONS_KEY,
    VERDICT_KEY,
    AuditedResearchAgent,
)


class ScriptedAgent(BaseAgent):
    """Emits the next scripted reply and stores it under ``state_key``."""

    replies: list[str]
    state_key: str
    fail: bool = False
    calls: int = 0

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        self.calls += 1
        if self.fail:
            raise RuntimeError("judge unavailable")
        text = self.replies[min(self.calls, len(self.replies)) - 1]
        yield Event(
            invocation_id=ctx.invocation_id,
            author=self.name,
            branch=ctx.branch,
            content=types.Content(role="model", parts=[types.Part(text=text)]),
            actions=EventActions(state_delta={self.state_key: text}),
        )


def _run(root: BaseAgent) -> dict[str, Any]:
    """Runs ``root`` once through a real ADK runner; returns session state."""

    async def _go() -> dict[str, Any]:
        runner = InMemoryRunner(app=App(root_agent=root, name="audit_test"))
        session = await runner.session_service.create_session(
            app_name="audit_test", user_id="u"
        )
        async for _ in runner.run_async(
            user_id="u",
            session_id=session.id,
            new_message=types.Content(
                role="user", parts=[types.Part(text="Compare Austin vs Ohio")]
            ),
        ):
            pass
        session = await runner.session_service.get_session(
            app_name="audit_test", user_id="u", session_id=session.id
        )
        return dict(session.state)

    return asyncio.run(_go())


def _loop(researcher_replies, judge_replies, judge_fails=False):
    researcher = ScriptedAgent(
        name="researcher", replies=researcher_replies, state_key=DRAFT_KEY
    )
    judge = ScriptedAgent(
        name="judge",
        replies=judge_replies,
        state_key=VERDICT_KEY,
        fail=judge_fails,
    )
    root = AuditedResearchAgent(
        name="audited", researcher=researcher, judge=judge, max_revisions=1
    )
    return root, researcher, judge


def test_approved_draft_is_not_revised():
    root, researcher, judge = _loop(["draft v1"], ["[APPROVE] looks right"])

    state = _run(root)

    assert (researcher.calls, judge.calls) == (1, 1)
    assert state[DRAFT_KEY] == "draft v1"
    assert state[VERDICT_KEY].startswith("[APPROVE]")
    assert state[REVISIONS_KEY] == 0


def test_rejected_draft_is_revised_once():
    root, researcher, judge = _loop(
        ["draft v1", "draft v2"],
        ["[REJECT] missing Ohio data", "[APPROVE] fixed"],
    )

    state = _run(root)

    assert (researcher.calls, judge.calls) == (2, 2)
    assert state[DRAFT_KEY] == "draft v2"
    assert state[VERDICT_KEY] == "[APPROVE] fixed"
    assert state[REVISIONS_KEY] == 1


def test_revisions_are_bounded_when_judge_keeps_rejecting():
    root, researcher, judge = _loop(
        ["draft v1", "draft v2", "draft v3"], ["[REJECT] still wrong"]
    )

    state = _run(root)

    # max_revisions=1: one revision, then stop, even though still rejected.
    assert (researcher.calls, judge.calls) == (2, 2)
    assert state[DRAFT_KEY] == "draft v2"
    assert state[REVISIONS_KEY] == 1


def test_judge_failure_keeps_draft_and_records_warning():
    root, researcher, _judge = _loop(["draft v1"], [], judge_fails=True)

    state = _run(root)

    assert researcher.calls == 1
    assert state[DRAFT_KEY] == "draft v1"
    assert state[VERDICT_KEY].startswith("⚠️ Judge verification failed")
    assert "RuntimeError" in state[VERDICT_KEY]
    assert state[REVISIONS_KEY] == 0


def test_get_app_wires_audited_root_agent(monkeypatch):
    from economic_research.agent import ERAAgent, tool_error_to_result

    monkeypatch.delenv("ERA_BYPASS_SUPERVISOR", raising=False)
    root = ERAAgent().get_app().root_agent

    assert isinstance(root, AuditedResearchAgent)
    assert isinstance(root.researcher, LlmAgent)
    assert root.researcher.output_key == DRAFT_KEY
    assert root.researcher.on_tool_error_callback is tool_error_to_result
    assert root.judge.output_key == VERDICT_KEY
    assert root.max_revisions == 1


def test_get_app_bypass_returns_plain_researcher(monkeypatch):
    from economic_research.agent import ERAAgent

    monkeypatch.setenv("ERA_BYPASS_SUPERVISOR", "true")
    root = ERAAgent().get_app().root_agent

    assert isinstance(root, LlmAgent)
    assert root.name == "economic_research"
    assert root.output_key == DRAFT_KEY
