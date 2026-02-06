import logging
from app.utils.utils import load_prompt_from_file
try:
    from google.adk.agents import Agent
except ImportError:
    from adk.agents import Agent
story_agent = None
try:
    MODEL = 'gemini-2.5-flash'
    DESCRIPTION = 'An agent that generates a short, engaging campfire story for scouts.'
    story_agent = Agent(model=MODEL, name='story_agent', description=load_prompt_from_file('story_agent_desc.txt'), instruction=load_prompt_from_file('story_agent.txt'), output_key='story')
    logging.info(f"✅ Agent '{story_agent.name}' created using model '{MODEL}'.")
except Exception as e:
    logging.error(f'❌ Could not create Story agent. Check API Key ({MODEL}). Error: {e}')