import logging
from google.adk.agents import Agent
from .utils.utils import load_prompt_from_file
logger = logging.getLogger(__name__)
MODEL = 'gemini-2.5-flash'
DESCRIPTION = 'Agent responsible for writing a screenplay based on a story'
screenplay_agent = None
try:
    screenplay_agent = Agent(model=MODEL, name='screenplay_agent', description=DESCRIPTION, instruction=load_prompt_from_file('screenplay_agent.txt'), output_key='screenplay')
    logger.info(f"✅ Agent '{screenplay_agent.name}' created using model '{MODEL}'.")
except Exception as e:
    logger.error(f'❌ Could not create Screenplay agent. Check API Key ({MODEL}). Error: {e}')