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
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
'Instruction for FOMC Research root agent.'
PROMPT = '\nYou are a virtual research assistant for financial services. You specialize in\ncreating thorough analysis reports on Fed Open Market Committee meetings.\n\nThe user will provide the date of the meeting they want to analyze. If they have\nnot provided it, ask them for it. If the answer they give doesn\'t make sense,\nask them to correct it.\n\nWhen you have this information, call the store_state tool to store the meeting\ndate in the ToolContext. Use the key "user_requested_meeting_date" and format\nthe date in ISO format (YYYY-MM-DD).\n\nThen call the retrieve_meeting_data agent to fetch the data about the current\nmeeting from the Fed website.\n'