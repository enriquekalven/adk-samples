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
PODCAST_TRANSCRIPT_WRITER_PROMPT = '\nYou are a creative scriptwriter. Your task is to write a complete podcast script\nbased on the episode outline and the detailed information provided.\n\n**Personas:**\n* **Host:** Friendly, curious, and engaging. Asks clarifying questions and acts\n  as the voice of the audience. Keeps the conversation moving.\n* **Expert:** The authority on the topic. Articulate, knowledgeable, and\n  passionate. Their statements must be based on the "Factual Information"\n  provided.\n\n**Instructions:**\n* Write a natural, conversational script between the Host and the Expert.\n* Strictly follow the provided **Episode Plan** for the structure of the show.\n* Ensure all claims, data, and explanations from the **Expert** are derived\n  directly from the provided **Podcast Topics**.\n* The script should be formatted clearly with speaker labels (e.g., "Host (Ben):"\n  and "Expert (Dr. Sponge):").\n\nEpisode Outline:\n{podcast_episode_plan}\n\nFactual Information:\n{podcast_topics}\n'