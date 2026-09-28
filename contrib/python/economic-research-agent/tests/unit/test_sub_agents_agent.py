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

import pytest

from economic_research.sub_agents.agent import JudgeAgent


def test_judge_agent_instantiation():
    """Test that the JudgeAgent.get_agent() successfully instantiates an ADK Agent."""
    try:
        judge = JudgeAgent()
        agent_instance = judge.get_agent()

        # Verify it has the correct name and type
        assert agent_instance.name == "Auditor_Judge"
        assert len(agent_instance.tools) > 0
    except ImportError as e:
        pytest.skip(
            f"Skipping test because ADK library or dependency is missing: {e}"
        )
    except Exception as e:
        # If we get a real exception (like a TypeError or NameError), that's a failure
        raise AssertionError(
            f"JudgeAgent instantiation failed with unexpected error: {e}"
        ) from e
