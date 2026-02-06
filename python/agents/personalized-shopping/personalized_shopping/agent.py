from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from .prompt import personalized_shopping_agent_instruction
from .tools.click import click
from .tools.search import search
root_agent = Agent(model='gemini-2.5-flash', name='personalized_shopping_agent', instruction=personalized_shopping_agent_instruction, tools=[FunctionTool(func=search), FunctionTool(func=click)])