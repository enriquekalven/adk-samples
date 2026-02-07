# Copyright 2025 Google LLC
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

from google.adk.agents.context_cache_config import ContextCacheConfig
'Defines the prompts in the Machine Learning Engineering Agent.'
SYSTEM_INSTRUCTION = 'You are a Machine Learning Engineering Multi Agent System.\n'
FRONTDOOR_INSTRUCTION = '\nYou are a machine learning engineer given a machine learning task for which to engineer a solution.\n\n    - If the user asks questions that can be answered directly, answer it directly without calling any additional agents.\n    - In this example, the task is the California Housing Task.\n    - If the user asks for a description of the task, then obtain the task, extract the description and return it. Do not execute the task.\n\n    # **Workflow:**\n\n    # 1. Obtain intent.\n\n    # 2. Obtain task\n\n    # 3. Carry out task\n\n\n    # **Tool Usage Summary:**\n\n    #   * **Greeting/Out of Scope:** answer directly.\n'
TASK_AGENT_INSTR = '# Introduction\n- Your task is to be a Kaggle grandmaster attending a competition.\n- In order to win this competition, you need to come up with an excellent solution in Python.\n- You need to first obtain a absolute path to the local directory that contains the data of the Kaggle competition from the user.\n'