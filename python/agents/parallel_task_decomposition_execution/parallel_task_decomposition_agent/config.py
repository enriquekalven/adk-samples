import logging
import os
from dotenv import load_dotenv
load_dotenv()
logger = logging.getLogger('google_adk.' + __name__)
GOOGLE_OAUTH_CREDENTIALS_FILENAME = os.environ.get('GOOGLE_OAUTH_CREDENTIALS')
GOOGLE_OAUTH_CREDENTIALS_PATH = ''
if GOOGLE_OAUTH_CREDENTIALS_FILENAME:
    GOOGLE_OAUTH_CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), GOOGLE_OAUTH_CREDENTIALS_FILENAME)
else:
    logger.warning('GOOGLE_OAUTH_CREDENTIALS environment variable is NOT set. This is required for the real Google Calendar tool.')
SLACK_MCP_XOXP_TOKEN = os.environ.get('SLACK_MCP_XOXP_TOKEN')
if not SLACK_MCP_XOXP_TOKEN:
    logger.warning('SLACK_MCP_XOXP_TOKEN environment variable is NOT set. This is required for the real Slack tool.')
GMAIL_CREDENTIALS_PATH = os.path.expanduser('~/.gmail-mcp/credentials.json')
if not os.path.exists(GMAIL_CREDENTIALS_PATH):
    logger.warning('Gmail credentials not found at ~/.gmail-mcp/credentials.json.')
    logger.warning("This is required for the real Gmail tool. Run 'npx @gongrzhe/server-gmail-autoauth-mcp auth'.")