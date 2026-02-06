"""Retrieve meeting data sub-agent for FOMC Research Agent"""
from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from ..agent import MODEL
from ..shared_libraries.callbacks import rate_limit_callback
from ..tools.fetch_page import fetch_page_tool
from . import retrieve_meeting_data_agent_prompt
from .extract_page_data_agent import ExtractPageDataAgent
RetrieveMeetingDataAgent = Agent(model=MODEL, name='retrieve_meeting_data_agent', description='Retrieve data about a Fed meeting from the Fed website', instruction=retrieve_meeting_data_agent_prompt.PROMPT, tools=[fetch_page_tool, AgentTool(ExtractPageDataAgent)], sub_agents=[], before_model_callback=rate_limit_callback)