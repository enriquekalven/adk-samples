# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
import os
from datetime import datetime
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.langchain_tool import LangchainTool
from google.adk.tools.mcp_tool import MCPToolset, StreamableHTTPConnectionParams
from langchain_community.tools import StackExchangeTool
from langchain_community.utilities import StackExchangeAPIWrapper
from toolbox_core import ToolboxSyncClient
load_dotenv()

def get_current_date() -> dict:
    """
    Get the current date in the format YYYY-MM-DD
    """
    return {'current_date': datetime.now().strftime('%Y-%m-%d')}
search_agent = Agent(model='gemini-2.5-flash', name='search_agent', instruction="\n    You're a specialist in Google Search.\n    ", tools=[google_search])
search_tool = AgentTool(search_agent)
stack_exchange_tool = StackExchangeTool(api_wrapper=StackExchangeAPIWrapper())
langchain_tool = LangchainTool(stack_exchange_tool)
TOOLBOX_URL = os.getenv('MCP_TOOLBOX_URL', 'http://127.0.0.1:5000')
try:
    toolbox = ToolboxSyncClient(TOOLBOX_URL)
    toolbox_tools = toolbox.load_toolset('tickets_toolset')
except Exception:
    toolbox_tools = []
try:
    mcp_tools = MCPToolset(connection_params=StreamableHTTPConnectionParams(url='https://api.githubcopilot.com/mcp/', headers={'Authorization': 'Bearer ' + os.getenv('GITHUB_PERSONAL_ACCESS_TOKEN')}), tool_filter=['search_repositories', 'search_issues', 'list_issues', 'get_issue', 'list_pull_requests', 'get_pull_request'])
except Exception:
    mcp_tools = None