from google.adk.agents import Agent
from .order_processing_tool import order_processing_tool
root_agent = Agent(model='gemini-2.5-flash', name='order_processing_agent', instruction='Help the user with creating orders, leverage the tools you have access to', tools=[order_processing_tool])