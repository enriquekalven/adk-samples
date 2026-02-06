from google.adk.agents.context_cache_config import ContextCacheConfig
from typing import Literal
from google.adk.agents.context_cache_config import ContextCacheConfig
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
'Database Agent: get data from database (BigQuery) using NL2SQL.'
import logging
import os
from typing import Any
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools import BaseTool, ToolContext
from google.adk.tools.bigquery import BigQueryToolset
from google.adk.tools.bigquery.config import BigQueryToolConfig, WriteMode
from google.genai import types
from ...utils.utils import USER_AGENT
from . import tools
from .chase_sql import chase_db_tools
from .prompts import return_instructions_bigquery
logger = logging.getLogger(__name__)
NL2SQL_METHOD = os.getenv('NL2SQL_METHOD', 'BASELINE')
ADK_BUILTIN_BQ_EXECUTE_SQL_TOOL = 'execute_sql'

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def setup_before_agent_call(callback_context: CallbackContext) -> None:
    """Setup the agent."""
    if 'database_settings' not in callback_context.state:
        callback_context.state['database_settings'] = tools.get_database_settings()

def store_results_in_context(tool: BaseTool, args: dict[str, Any], tool_context: ToolContext, tool_response: dict) -> dict | None:
    if tool.name == ADK_BUILTIN_BQ_EXECUTE_SQL_TOOL:
        if tool_response['status'] == 'SUCCESS':
            tool_context.state['bigquery_query_result'] = tool_response['rows']
    return None
bigquery_tool_filter = [ADK_BUILTIN_BQ_EXECUTE_SQL_TOOL]
bigquery_tool_config = BigQueryToolConfig(write_mode=WriteMode.BLOCKED, application_name=USER_AGENT)
bigquery_toolset = BigQueryToolset(tool_filter=bigquery_tool_filter, bigquery_tool_config=bigquery_tool_config)
bigquery_agent = LlmAgent(model=os.getenv('BIGQUERY_AGENT_MODEL', ''), name='bigquery_agent', instruction=return_instructions_bigquery(), tools=[chase_db_tools.initial_bq_nl2sql if NL2SQL_METHOD == 'CHASE' else tools.bigquery_nl2sql, bigquery_toolset], before_agent_callback=setup_before_agent_call, after_tool_callback=store_results_in_context, generate_content_config=types.GenerateContentConfig(temperature=0.01), context_cache_config=ContextCacheConfig(min_tokens=2048, ttl_seconds=600))