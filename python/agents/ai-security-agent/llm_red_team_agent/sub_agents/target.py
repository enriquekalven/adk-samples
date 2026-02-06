from google.adk.agents import LlmAgent
from google.genai import types
from ..config import config
from ..safety_rules import BANKING_AGENT_IDENTITY, BANKING_SAFETY_CONSTITUTION
system_prompt = f'\n    {BANKING_AGENT_IDENTITY}\n    {BANKING_SAFETY_CONSTITUTION}\n    When answering the user, adhere strictly to these protocols.\n    '

def create() -> LlmAgent:
    return LlmAgent(name='target', model=config.target_model, instruction=system_prompt, generate_content_config=types.GenerateContentConfig(temperature=0.1))