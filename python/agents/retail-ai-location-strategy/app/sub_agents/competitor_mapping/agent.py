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
'Competitor Mapping Agent - Part 2A of the Location Strategy Pipeline.\n\nThis agent maps competitors using the Google Maps Places API to get\nground-truth data about existing businesses in the target area.\n'
from google.adk.agents import LlmAgent
from google.genai import types
from ...callbacks import after_competitor_mapping, before_competitor_mapping
from ...config import FAST_MODEL, RETRY_ATTEMPTS, RETRY_INITIAL_DELAY
from ...tools import search_places
COMPETITOR_MAPPING_INSTRUCTION = 'You are a market intelligence analyst specializing in competitive landscape analysis.\n\nYour task is to map and analyze all competitors in the target area using real Google Maps data.\n\nTARGET LOCATION: {target_location}\nBUSINESS TYPE: {business_type}\nCURRENT DATE: {current_date}\n\n## Your Mission\nUse the search_places function to get REAL data from Google Maps about existing competitors.\n\n## Step 1: Search for Competitors\nCall the search_places function with queries like:\n- "{business_type} near {target_location}"\n- Related business types in the same area\n\n## Step 2: Analyze the Results\nFor each competitor found, note:\n- Business name\n- Location/address\n- Rating (out of 5)\n- Number of reviews\n- Business status (operational, etc.)\n\n## Step 3: Identify Patterns\nAnalyze the competitive landscape:\n\n### Geographic Clustering\n- Are competitors clustered in specific areas/zones?\n- Which areas have high concentration vs sparse presence?\n- Are there any "dead zones" with no competitors?\n\n### Location Types\n- Shopping malls and retail areas\n- Main roads and commercial corridors\n- Residential neighborhoods\n- Near transit (metro stations, bus stops)\n\n### Quality Segmentation\n- Premium tier: High-rated (4.5+), likely higher prices\n- Mid-market: Ratings 4.0-4.4\n- Budget tier: Lower ratings or basic offerings\n- Chain vs independent businesses\n\n## Step 4: Strategic Assessment\nProvide insights on:\n- Which areas appear saturated with competitors?\n- Which areas might be underserved opportunities?\n- What quality gaps exist (e.g., no premium options)?\n- Where are the strongest competitors located?\n\n## Output Format\nProvide a detailed competitor map with:\n1. List of all competitors found with their details\n2. Zone-by-zone breakdown of competition\n3. Pattern analysis and clustering insights\n4. Strategic opportunities and saturation warnings\n\nBe specific and reference the actual data you receive from the search_places tool.\n'
competitor_mapping_agent = LlmAgent(name='CompetitorMappingAgent', model=FAST_MODEL, description='Maps competitors using Google Maps Places API for ground-truth competitor data', instruction=COMPETITOR_MAPPING_INSTRUCTION, generate_content_config=types.GenerateContentConfig(http_options=types.HttpOptions(retry_options=types.HttpRetryOptions(initial_delay=RETRY_INITIAL_DELAY, attempts=RETRY_ATTEMPTS))), tools=[search_places], output_key='competitor_analysis', before_agent_callback=before_competitor_mapping, after_agent_callback=after_competitor_mapping, context_cache_config=ContextCacheConfig(min_tokens=2048, ttl_seconds=600))