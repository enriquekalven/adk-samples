from typing import Literal
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from google.adk.agents.context_cache_config import ContextCacheConfig
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from google.adk.agents.context_cache_config import ContextCacheConfig
"Intake Agent - Extracts target location and business type from user request.\n\nThis agent parses the user's natural language request and extracts the\nrequired parameters (target_location, business_type) into session state\nfor use by subsequent agents in the pipeline.\n"
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.genai import types
from pydantic import BaseModel, Field
from ...config import FAST_MODEL, RETRY_ATTEMPTS, RETRY_INITIAL_DELAY

class UserRequest(BaseModel):
    """Structured output for parsing user's location strategy request."""
    target_location: str = Field(description="The geographic location/area to analyze (e.g., 'Indiranagar, Bangalore', 'Manhattan, New York')")
    business_type: str = Field(description="The type of business the user wants to open (e.g., 'coffee shop', 'bakery', 'gym', 'restaurant')")
    additional_context: str | None = Field(default=None, description='Any additional context or requirements mentioned by the user')

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def after_intake(callback_context: CallbackContext) -> types.Content | None:
    """After intake, copy the parsed values to state for other agents."""
    parsed = callback_context.state.get('parsed_request', {})
    if isinstance(parsed, dict):
        callback_context.state['target_location'] = parsed.get('target_location', '')
        callback_context.state['business_type'] = parsed.get('business_type', '')
        callback_context.state['additional_context'] = parsed.get('additional_context', '')
    elif hasattr(parsed, 'target_location'):
        callback_context.state['target_location'] = parsed.target_location
        callback_context.state['business_type'] = parsed.business_type
        callback_context.state['additional_context'] = parsed.additional_context or ''
    stages = callback_context.state.get('stages_completed', [])
    stages.append('intake')
    callback_context.state['stages_completed'] = stages
    return None
INTAKE_INSTRUCTION = 'You are a request parser for a retail location intelligence system.\n\nYour task is to extract the target location and business type from the user\'s request.\n\n## Examples\n\nUser: "I want to open a coffee shop in Indiranagar, Bangalore"\n→ target_location: "Indiranagar, Bangalore"\n→ business_type: "coffee shop"\n\nUser: "Analyze the market for a new gym in downtown Seattle"\n→ target_location: "downtown Seattle"\n→ business_type: "gym"\n\nUser: "Help me find the best location for a bakery in Mumbai"\n→ target_location: "Mumbai"\n→ business_type: "bakery"\n\nUser: "Where should I open my restaurant in San Francisco\'s Mission District?"\n→ target_location: "Mission District, San Francisco"\n→ business_type: "restaurant"\n\n## Instructions\n1. Extract the geographic location mentioned by the user\n2. Identify the type of business they want to open\n3. Note any additional context or requirements\n\nIf the user doesn\'t specify a clear location or business type, make a reasonable inference or ask for clarification.\n'
intake_agent = LlmAgent(name='IntakeAgent', model=FAST_MODEL, description='Parses user request to extract target location and business type', instruction=INTAKE_INSTRUCTION, generate_content_config=types.GenerateContentConfig(http_options=types.HttpOptions(retry_options=types.HttpRetryOptions(initial_delay=RETRY_INITIAL_DELAY, attempts=RETRY_ATTEMPTS))), output_schema=UserRequest, output_key='parsed_request', after_agent_callback=after_intake, context_cache_config=ContextCacheConfig(min_tokens=2048, ttl_seconds=600))