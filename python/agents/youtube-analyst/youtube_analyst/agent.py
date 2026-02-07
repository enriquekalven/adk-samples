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

import os
from google import genai
from google.adk.agents import Agent
from google.adk.tools import load_artifacts
from .config import config
from .tools import analyze_sentiment_heuristic, calculate_engagement_metrics, calculate_match_score, get_channel_details, get_current_date_time, get_date_range, get_video_comments, get_video_details, render_html, search_youtube
from .utils import load_prompt
from .visualization_agent import visualization_agent
youtube_agent = Agent(model=config.agent_settings.model, name='youtube_agent', description='Agent for YouTube analysis and data retrieval', instruction=load_prompt(os.path.dirname(__file__), 'youtube_agent.txt'), sub_agents=[visualization_agent], tools=[search_youtube, get_video_details, get_channel_details, get_video_comments, calculate_engagement_metrics, calculate_match_score, analyze_sentiment_heuristic, get_current_date_time, get_date_range, render_html, load_artifacts], generate_content_config=genai.types.GenerateContentConfig(max_output_tokens=config.YOUTUBE_AGENT_MAX_OUTPUT_TOKENS))
root_agent = youtube_agent