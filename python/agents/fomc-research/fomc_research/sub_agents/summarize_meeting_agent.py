"""Summarize the content of the FOMC meeting transcript."""
from google.adk.agents import Agent
from ..agent import MODEL
from ..shared_libraries.callbacks import rate_limit_callback
from ..tools.store_state import store_state_tool
from . import summarize_meeting_agent_prompt
SummarizeMeetingAgent = Agent(name='summarize_meeting_agent', model=MODEL, description='Summarize the content and sentiment of the latest FOMC meeting.', instruction=summarize_meeting_agent_prompt.PROMPT, tools=[store_state_tool], before_model_callback=rate_limit_callback)