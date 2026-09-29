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

"""Researcher -> Auditor Judge -> optional revision, as one ADK agent.

Wrapping the actor-critic loop in a custom agent makes it part of
``root_agent``. That means every entrypoint gets the audit: Agent Runtime
(``AdkApp``), the ADK web playground, the FastAPI server and
``ERAAgent.query()``. Before, only ``query()`` ran the judge.
"""

import logging
from collections.abc import AsyncGenerator

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions

logger = logging.getLogger(__name__)

# Session-state keys shared with ERAAgent.query().
DRAFT_KEY = "draft_report"
VERDICT_KEY = "judge_verdict"
REVISIONS_KEY = "audit_revisions"

# The judge starts its verdict with this marker to request a revision.
REJECT_MARKER = "[REJECT]"


class AuditedResearchAgent(BaseAgent):
    """Runs the researcher, has the judge audit it, and revises on rejection.

    The researcher must write its report to ``DRAFT_KEY`` and the judge its
    verdict to ``VERDICT_KEY`` (via ``output_key``). On a revision pass the
    researcher sees the judge's feedback in the shared conversation history.
    """

    researcher: BaseAgent
    judge: BaseAgent
    max_revisions: int = 1

    def __init__(
        self,
        *,
        name: str,
        researcher: BaseAgent,
        judge: BaseAgent,
        max_revisions: int = 1,
        description: str = "",
    ) -> None:
        super().__init__(
            name=name,
            description=description,
            researcher=researcher,
            judge=judge,
            max_revisions=max_revisions,
            sub_agents=[researcher, judge],
        )

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        revisions = 0
        state_delta: dict[str, object] = {}

        while True:
            async for event in self.researcher.run_async(ctx):
                yield event

            try:
                async for event in self.judge.run_async(ctx):
                    yield event
            except Exception as exc:  # degrade, don't fail
                # A broken judge (quota, search outage) must not discard a
                # finished research draft. Record why the audit is missing.
                logger.warning(
                    "Auditor judge failed; returning unaudited draft: %s",
                    type(exc).__name__,
                )
                state_delta[VERDICT_KEY] = (
                    f"⚠️ Judge verification failed: {type(exc).__name__}"
                )
                break

            verdict = str(ctx.session.state.get(VERDICT_KEY) or "")
            if REJECT_MARKER not in verdict:
                break
            if revisions >= self.max_revisions:
                logger.info(
                    "Judge still rejects after %d revision(s); stopping.",
                    revisions,
                )
                break
            revisions += 1

        state_delta[REVISIONS_KEY] = revisions
        yield Event(
            invocation_id=ctx.invocation_id,
            author=self.name,
            branch=ctx.branch,
            actions=EventActions(state_delta=state_delta),
        )
