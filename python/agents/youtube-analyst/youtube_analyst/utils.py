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

def load_prompt(base_dir: str, filename: str) -> str:
    """
    Loads a prompt text from a file.

    Args:
        base_dir: The directory containing the 'prompts' subdirectory.
                  Typically passed as os.path.dirname(__file__) from the calling agent.
        filename: The name of the prompt file (e.g., 'agent_prompt.txt').

    Returns:
        The content of the prompt file.
    """
    prompt_path = os.path.join(base_dir, 'prompts', filename)
    with open(prompt_path) as f:
        return f.read()