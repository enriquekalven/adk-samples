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

import logging
import os
from dotenv import load_dotenv
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import MCPToolset, StreamableHTTPConnectionParams
logger = logging.getLogger(__name__)
logging.basicConfig(format='[%(levelname)s]: %(message)s', level=logging.INFO)
load_dotenv()
SYSTEM_INSTRUCTION = "You are a specialized assistant for currency conversions. Your sole purpose is to use the 'get_exchange_rate' tool to answer questions about currency exchange rates. If the user asks about anything other than currency conversion or exchange rates, politely state that you cannot help with that topic and can only assist with currency-related queries. Do not attempt to answer unrelated questions or use tools for other purposes."
logger.info('--- 🔧 Loading MCP tools from MCP Server... ---')
logger.info('--- 🤖 Creating ADK Currency Agent... ---')
root_agent = LlmAgent(model='gemini-2.5-flash', name='currency_agent', description='An agent that can help with currency conversions', instruction=SYSTEM_INSTRUCTION, tools=[MCPToolset(connection_params=StreamableHTTPConnectionParams(url=os.getenv('MCP_SERVER_URL', 'http://localhost:8080/mcp')))])
a2a_app = to_a2a(root_agent, port=10000)