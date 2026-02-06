from tenacity import retry, wait_exponential, stop_after_attempt
import logging
from google.adk.tools import MCPToolset
logger = logging.getLogger(__name__)

def deep_code_review(file_content: str) -> str:
    """Performs a deep architectural and security review using Gemini Code Assist patterns.

    Args:
        file_content (str): The source code to analyze.

    Returns:
        str: A detailed critique based on developer-centric best practices.
    """
    return f'ANALYSIS_REQUEST: Review the following code for linting, security vulnerabilities, and ADK architectural compliance:\n\n{file_content}'

def get_mcp_tools(server_url: str):
    """Dynamically loads developer tools from an MCP server.

    Args:
        server_url (str): The endpoint of the MCP server.

    Returns:
        MCPToolset: A toolset containing discovered tools.
    """
    logger.info('Connecting to MCP server at %s', server_url)
    return MCPToolset(url=server_url)