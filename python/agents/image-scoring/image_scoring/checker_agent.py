from google.adk.agents import Agent
from . import config
from .prompt import CHECKER_PROMPT
from .tools.loop_condition_tool import check_tool_condition
checker_agent_instance = Agent(name='checker_agent', model=config.GENAI_MODEL, instruction=CHECKER_PROMPT, tools=[check_tool_condition], output_key='checker_output')