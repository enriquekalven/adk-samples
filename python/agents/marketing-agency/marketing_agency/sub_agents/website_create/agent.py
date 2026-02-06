"""website_create_agent: for creating beautiful web site"""
from google.adk import Agent
from . import prompt
MODEL = 'gemini-2.5-pro'
website_create_agent = Agent(model=MODEL, name='website_create_agent', instruction=prompt.WEBSITE_CREATE_PROMPT, output_key='website_create_output')