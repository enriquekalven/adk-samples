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
'Report Generator Agent - Part 4 of the Location Strategy Pipeline.\n\nThis agent generates a professional HTML executive report from the\nstructured LocationIntelligenceReport data using the generate_html_report tool.\n\nThe tool handles:\n- Calling Gemini to generate 7-slide McKinsey/BCG style HTML\n- Saving the HTML as an artifact for download in adk web\n'
from google.adk.agents import LlmAgent
from google.genai import types
from ...callbacks import after_report_generator, before_report_generator
from ...config import FAST_MODEL, RETRY_ATTEMPTS, RETRY_INITIAL_DELAY
from ...tools import generate_html_report
REPORT_GENERATOR_INSTRUCTION = 'You are an executive report generator for location intelligence analysis.\n\nYour task is to create a professional HTML executive report using the generate_html_report tool.\n\nTARGET LOCATION: {target_location}\nBUSINESS TYPE: {business_type}\nCURRENT DATE: {current_date}\n\n## Strategic Report Data\n{strategic_report}\n\n## Your Mission\nFormat the strategic report data and call the generate_html_report tool to create a\nMcKinsey/BCG-style 7-slide HTML presentation.\n\n## Steps\n\n### Step 1: Format the Report Data\nPrepare a comprehensive data summary from the strategic report above, including:\n- Analysis overview (location, business type, date, market validation)\n- Top recommendation details (location, score, opportunity type, strengths, concerns)\n- Competition metrics (total competitors, density, chain dominance, ratings)\n- Market characteristics (population, income, infrastructure, foot traffic, rental costs)\n- Alternative locations (name, score, strength, concern, why not top)\n- Next steps (actionable items)\n- Key insights (strategic observations)\n- Methodology summary\n\n### Step 2: Call the Tool\nCall the generate_html_report tool with the formatted report data.\nThe tool will:\n- Generate a professional 7-slide HTML report\n- Save it as an artifact named "executive_report.html"\n- Return the status and artifact details\n\n### Step 3: Report Result\nAfter the tool returns, confirm the report was generated successfully.\nIf there was an error, report what went wrong.\n'
report_generator_agent = LlmAgent(name='ReportGeneratorAgent', model=FAST_MODEL, description='Generates professional McKinsey/BCG-style HTML executive reports using the generate_html_report tool', instruction=REPORT_GENERATOR_INSTRUCTION, generate_content_config=types.GenerateContentConfig(http_options=types.HttpOptions(retry_options=types.HttpRetryOptions(initial_delay=RETRY_INITIAL_DELAY, attempts=RETRY_ATTEMPTS))), tools=[generate_html_report], output_key='report_generation_result', before_agent_callback=before_report_generator, after_agent_callback=after_report_generator, context_cache_config=ContextCacheConfig(min_tokens=2048, ttl_seconds=600))