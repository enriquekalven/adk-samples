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
'Defines the prompts for debugging.'
BUG_SUMMARY_INSTR = '# Error report\n{bug}\n\n# Your task\n- Remove all unnecessary parts of the above error report.\n- We are now running {filename}.py. Do not remove where the error occurred.'
BUG_REFINE_INSTR = '# Task description\n{task_description}\n\n# Code with an error:\n{code}\n\n# Error:\n{bug}\n\n# Your task\n- Please revise the code to fix the error.\n- If the error is a \'module not found` error, then install the necessary module. You can use `pip install <module>`, where `<module>` is the name of the module to install.\n- Do not remove subsampling if exists.\n- Provide the improved, self-contained Python script again.\n- There should be no additional headings or text in your response.\n- All the provided input data is stored in "./input" directory.\n- Remember to print a line in the code with \'Final Validation Performance: {{final_validation_score}}\' so we can parse performance.\n- The code should be a single-file python program that is self-contained and can be executed as-is.\n- Your response should only contain a single code block.\n- Do not use exit() function in the refined Python code.'