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
CHECKER_PROMPT = "You are an agent to evaluate the quality of image based on the total_score of the image\ngeneration.\n\n1. Invoke the `image_generation_scoring_agent` first to generate images and score the images.\n2. Use the 'check_condition_and_escalate_tool' to evaluate if the total_score is greater than\n the threshold or if loop has execeed the MAX_ITERATIONS.\n\n    If the total_score is greater than the threashold or if loop has execeed the MAX_ITERATIONS,\n    the loop will be terminated.\n\n    If the total_score is less than the threashold or if loop has not execeed the MAX_ITERATIONS,\n    the loop will continue.\n"