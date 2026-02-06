from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
import logging
import subprocess
from typing import Any
import google.auth
import google.auth.transport.requests
from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.oauth2 import id_token
from .config import DATAPLEX_MCP_SERVER_URL

class SafeMCPToolset(McpToolset):
    """
    A wrapper around MCPToolset that catches connection errors during tool retrieval.
    This ensures that if the MCP server is down, the agent can still function
    (albeit without the MCP tools) instead of crashing.
    """

    @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
    async def get_tools(self, *args: Any, **kwargs: Any) -> list[Any]:
        try:
            return await super().get_tools(*args, **kwargs, timeout=10, timeout=10)
        except Exception as e:
            logging.error(f'Failed to connect to MCP server or retrieve tools: {e}')
            logging.warning('Continuing without MCP tools.')
            return []

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def _get_dataplex_mcp_toolset():
    """
    Connects to the Dataplex MCP server using ID token authentication.
    """
    if not DATAPLEX_MCP_SERVER_URL:
        logging.info('DATAPLEX_MCP_SERVER_URL not configured. Skipping MCP toolset registration.')
        return None
    mcp_url = f'{DATAPLEX_MCP_SERVER_URL}/sse'
    token = None
    try:
        token = subprocess.check_output(['gcloud', 'auth', 'print-identity-token'], text=True).strip()
    except Exception as e:
        logging.warning(f'Failed to get ID token via gcloud: {e}')
    if not token:
        try:
            auth_req = google.auth.transport.requests.Request()
            target_audience = DATAPLEX_MCP_SERVER_URL
            token = id_token.fetch_id_token(auth_req, target_audience)
        except Exception as e:
            logging.error(f'Failed to get ID token for MCP server via library: {e}')
            return None
    return SafeMCPToolset(connection_params=SseConnectionParams(url=mcp_url, headers={'Authorization': f'Bearer {token}'}))