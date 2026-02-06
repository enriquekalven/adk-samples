"""marketing_create_agent: for creating marketing strategies"""
from google.adk import Agent
from . import prompt
MODEL = 'gemini-2.5-pro'
marketing_create_agent = Agent(model=MODEL, name='marketing_create_agent', instruction=prompt.MARKETING_CREATE_PROMPT, output_key='marketing_create_output')