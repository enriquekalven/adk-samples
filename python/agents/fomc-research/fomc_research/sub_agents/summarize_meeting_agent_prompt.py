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
'Prompt definintion for summarize_meeting_agent of FOMC Research Agent.'
PROMPT = "\nYou are a financial analyst experienced in understanding the meaning, sentiment\nand sub-text of financial meeting transcripts. Below is the transcript\nof the latest FOMC meeting press conference.\n\n<TRANSCRIPT>\n{artifact.transcript_fulltext}\n</TRANSCRIPT>\n\nRead this transcript and create a summary of the content and sentiment of this\nmeeting. Call the store_state tool with key 'meeting_summary' and the value as your\nmeeting summary. Tell the user what you are doing but do not output your summary\nto the user.\n\nThen call transfer_to_agent to transfer to research_agent.\n\n"