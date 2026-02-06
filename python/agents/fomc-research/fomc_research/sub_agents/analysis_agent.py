"""Analyze the research output for the FOMC Research Agent."""
from google.adk.agents import Agent
from ..agent import MODEL
from ..shared_libraries.callbacks import rate_limit_callback
from . import analysis_agent_prompt
AnalysisAgent = Agent(model=MODEL, name='analysis_agent', description='Analyze inputs and determine implications for future FOMC actions.', instruction=analysis_agent_prompt.PROMPT, before_model_callback=rate_limit_callback)