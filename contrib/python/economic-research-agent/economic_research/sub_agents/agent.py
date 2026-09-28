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

import os

from google.adk.agents import Agent
from google.adk.models import Gemini

from economic_research.shared_libraries.helper import get_default_model

from .prompt import JudgePrompts
from .tools.search_skill import web_search_skill

prompts = JudgePrompts()
JUDGE_INSTRUCTIONS = prompts.auditor_judge_instructions()


class JudgeAgent:
    def __init__(self):
        pass

    def get_agent(self) -> Agent:
        """
        Instantiates the Auditor Judge agent using ADK.
        """
        tools = [web_search_skill]

        # We use Gemini 3.5 Flash as a lightweight, fast auditor
        resolved_model = get_default_model(os.getenv("MODEL_NAME"))
        return Agent(
            name="Auditor_Judge",
            model=Gemini(model=resolved_model),
            instruction=JUDGE_INSTRUCTIONS,
            tools=tools,
        )
