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