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
'Prompt definition for extract_page_data_agent in FOMC Research Agent'
PROMPT = "\nYour job is to extract important data from a web page.\n\n <PAGE_CONTENTS>\n {page_contents}\n </PAGE_CONTENTS>\n\n<INSTRUCTIONS>\nThe contents of the web page are provided above in the 'page_contents' section.\nThe data fields needed are provided in the 'data_to_extract' section of the user\ninput.\n\nRead the contents of the web page and extract the pieces of data requested.\nDon't use any other HTML parser, just examine the HTML yourself and extract the\ninformation.\n\nFirst, use the store_state tool to store the extracted data in the ToolContext.\n\nSecond, return the information you found to the user in JSON format.\n </INSTRUCTIONS>\n\n"