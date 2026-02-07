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
PROMPT = '\n Your primary objective: Transform the input text into a pair of highly optimized prompts—one positive and\n one negative—specifically designed for generating a visually compelling,\n rule-compliant lockscreen image using the Imagen3 text-to-image model (provided by Google/GCP).\n    Critical First Step: Before constructing any prompts, you must first analyze the\n    input text to identify or conceptualize a primary subject. This subject MUST:\n    1. Be very much related to the input text presented. The viewer should\n     feel that the generated image of that subject is conveying\n    what he/she is reading from that new article.\n    2. It should not  violate any content restrictions (especially regarding humans,\n    politics, religion, etc.).\n    3. Describe in detail on what we would like to represent around the primary subject,\n      as-in, paint a complete picture.\n\n    This chosen subject will be the cornerstone of your "Image Generation Prompt".\n\n    Invoke the \'get_policy_text\' tool to obtain the \'policy_text\'. The \'policy_text\'\n    defines the rules for the image generation.\n    The image also should comply with rules defined in the \'policy_text\'.\n\n    Negative Prompt: Generate a negative prompt to ensure the image does not\n    violate the rules defined in the \'policy_text\'.\n\n    '