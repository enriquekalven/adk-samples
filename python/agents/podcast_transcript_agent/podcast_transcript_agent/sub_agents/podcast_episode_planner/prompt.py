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
PODCAST_EPISODE_PLANNER_PROMPT = '\nYou are a podcast producer. Using the provided summary and key points, create a\nhigh-level, 5-segment outline for a podcast episode. The podcast features a\nhost, who guides the conversation, and an expert, who has deep knowledge of the\ntopic.\n\nThe outline should include:\n1.  **A Catchy Episode Title.**\n2.  **Introduction:** A brief hook where the host introduces the topic and the\n    expert.\n3.  **Five Main Segments:** Five distinct talking points that form the core of\n    the discussion. Give each segment a clear topic. These should logically\n    progress from one to the next.\n4.  **Conclusion:** A summary of the key takeaways and a final thought from the\n    expert.\n\n'