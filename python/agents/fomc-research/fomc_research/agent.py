"""FOMC Research sample agent."""
import logging
import warnings
from google.adk.agents import Agent
from . import MODEL, root_agent_prompt
from .shared_libraries.callbacks import rate_limit_callback
from .sub_agents.analysis_agent import AnalysisAgent
from .sub_agents.research_agent import ResearchAgent
from .sub_agents.retrieve_meeting_data_agent import RetrieveMeetingDataAgent
from .tools.store_state import store_state_tool
warnings.filterwarnings('ignore', category=UserWarning, module='.*pydantic.*')
logger = logging.getLogger(__name__)
logger.debug('Using MODEL: %s', MODEL)
root_agent = Agent(model=MODEL, name='root_agent', description='Use tools and other agents provided to generate an analysis reportabout the most recent FOMC meeting.', instruction=root_agent_prompt.PROMPT, tools=[store_state_tool], sub_agents=[RetrieveMeetingDataAgent, ResearchAgent, AnalysisAgent], before_model_callback=rate_limit_callback)