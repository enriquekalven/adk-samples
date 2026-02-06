from google.adk.agents import Agent
from .snow_connector_tool import snow_connector_tool
root_agent = Agent(name='snow_agent', description='ServiceNow agent that allows you to manage and create Incidents', instruction='Help the user with getting, listing and creating ServiceNow incidents, leverage the tools you have access to', tools=[snow_connector_tool], model='gemini-2.5-pro')