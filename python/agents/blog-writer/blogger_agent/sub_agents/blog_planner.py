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
from google.adk.agents import Agent, LoopAgent
from google.adk.tools import google_search
from ..agent_utils import suppress_output_callback
from ..config import config
from ..validation_checkers import OutlineValidationChecker
blog_planner = Agent(model=config.worker_model, name='blog_planner', description='Generates a blog post outline.', instruction='\n    You are a technical content strategist. Your job is to create a blog post outline.\n    The outline should be well-structured and easy to follow.\n    It should include a title, an introduction, a main body with several sections, and a conclusion.\n    If a codebase is provided, the outline should include sections for code snippets and technical deep dives.\n    The codebase context will be available in the `codebase_context` state key.\n    Use the information in the `codebase_context` to generate a specific and accurate outline.\n    Use Google Search to find relevant information and examples to support your writing.\n    Your final output should be a blog post outline in Markdown format.\n    ', tools=[google_search], output_key='blog_outline', after_agent_callback=suppress_output_callback, context_cache_config=ContextCacheConfig(min_tokens=2048, ttl_seconds=600))
robust_blog_planner = LoopAgent(name='robust_blog_planner', description='A robust blog planner that retries if it fails.', sub_agents=[blog_planner, OutlineValidationChecker(name='outline_validation_checker')], max_iterations=3, after_agent_callback=suppress_output_callback)