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

from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
import datetime
import os
import uuid
from zoneinfo import ZoneInfo
import google.auth
from google.adk.agents import LoopAgent, SequentialAgent
from google.adk.agents.callback_context import CallbackContext
from .checker_agent import checker_agent_instance
from .sub_agents.image import image_generation_agent
from .sub_agents.prompt import image_generation_prompt_agent
from .sub_agents.scoring import scoring_images_prompt
_, project_id = google.auth.default()
os.environ.setdefault('GOOGLE_CLOUD_PROJECT', project_id)
os.environ['GOOGLE_CLOUD_LOCATION'] = 'global'
os.environ.setdefault('GOOGLE_GENAI_USE_VERTEXAI', 'True')

def set_session(callback_context: CallbackContext):
    """
    Sets a unique ID and timestamp in the callback context's state.
    This function is called before the main_loop_agent executes.
    """
    callback_context.state['unique_id'] = str(uuid.uuid4())
    callback_context.state['timestamp'] = datetime.datetime.now(ZoneInfo('UTC')).isoformat()
image_generation_scoring_agent = SequentialAgent(name='image_generation_scoring_agent', description='\n        Analyzes a input text and creates the image generation prompt, generates the relevant images with imagen3 and scores the images."\n        1. Invoke the image_generation_prompt_agent agent to generate the prompt for generating images\n        2. Invoke the image_generation_agent agent to generate the images\n        3. Invoke the scoring_images_prompt agent to score the images\n            ', sub_agents=[image_generation_prompt_agent, image_generation_agent, scoring_images_prompt])
image_scoring = LoopAgent(name='image_scoring', description='Repeatedly runs a sequential process and checks a termination condition.', sub_agents=[image_generation_scoring_agent, checker_agent_instance], before_agent_callback=set_session)
root_agent = image_scoring