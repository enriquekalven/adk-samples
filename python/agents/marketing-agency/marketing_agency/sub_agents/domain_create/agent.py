"""Domain_create_agent: for suggesting meanigful DNS domain"""
from google.adk import Agent
from google.adk.tools import google_search
from . import prompt
MODEL = 'gemini-2.5-pro'
domain_create_agent = Agent(model=MODEL, name='domain_create_agent', instruction=prompt.DOMAIN_CREATE_PROMPT, output_key='domain_create_output', tools=[google_search])