from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
'\nGmail Manager using LangChain Community Gmail Toolkit.\nThis module provides robust Gmail operations with built-in error handling and features.\n'
import logging
import os
from datetime import datetime
from dotenv import load_dotenv
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from langchain_community.agent_toolkits import GmailToolkit
    from langchain_community.tools.gmail.get_message import GmailGetMessage
    from langchain_community.tools.gmail.get_thread import GmailGetThread
    from langchain_community.tools.gmail.search import GmailSearch
    from langchain_community.tools.gmail.send_message import GmailSendMessage
    from langchain_community.tools.gmail.utils import build_resource_service
    LANGCHAIN_GMAIL_AVAILABLE = True
except ImportError as e:
    logging.warning(f'LangChain Gmail toolkit not available: {e}')
    LANGCHAIN_GMAIL_AVAILABLE = False
load_dotenv()
SCOPES = ['https://www.googleapis.com/auth/gmail.send', 'https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.compose', 'https://www.googleapis.com/auth/gmail.modify']

class LangChainGmailManager:
    """
    Gmail manager using LangChain Community Gmail Toolkit.
    Provides robust Gmail operations with built-in error handling and features.
    """

    def __init__(self):
        self.service = None
        self.toolkit = None
        self.tools = {}
        self.credentials_file = os.path.join(os.path.dirname(__file__), 'gmail_credentials.json')
        self.token_file = os.path.join(os.path.dirname(__file__), 'gmail_token.json')
        if LANGCHAIN_GMAIL_AVAILABLE:
            self.initialize_gmail_toolkit()
        else:
            logging.error('LangChain Gmail toolkit not available. Please install: pip install langchain-community')

    @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
    def initialize_gmail_toolkit(self) -> bool:
        """Initialize LangChain Gmail toolkit with proper authentication."""
        try:
            credentials = self._get_gmail_credentials()
            if not credentials:
                logging.error('Failed to obtain Gmail credentials')
                return False
            self.service = build_resource_service(credentials=credentials)
            self.toolkit = GmailToolkit()
            self._setup_tools()
            logging.info('LangChain Gmail Toolkit initialized successfully')
            return True
        except Exception as e:
            logging.error(f'Failed to initialize LangChain Gmail toolkit: {e}')
            return False

    @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
    def _get_gmail_credentials(self) -> Credentials | None:
        """Get Gmail credentials using OAuth2 flow."""
        creds = None
        if os.path.exists(self.token_file):
            try:
                creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
            except Exception as e:
                logging.warning(f'Failed to load existing token: {e}')
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logging.warning(f'Failed to refresh token: {e}')
                    creds = None
            if not creds:
                if os.path.exists(self.credentials_file):
                    try:
                        flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, SCOPES)
                        creds = flow.run_local_server(port=0)
                    except Exception as e:
                        logging.error(f'OAuth2 flow failed: {e}')
                        return None
                else:
                    logging.error(f'Gmail credentials file not found: {self.credentials_file}')
                    return None
            if creds:
                try:
                    with open(self.token_file, 'w') as token:
                        token.write(creds.to_json())
                except Exception as e:
                    logging.warning(f'Failed to save token: {e}')
        return creds

    @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
    def _setup_tools(self):
        """Set up individual LangChain Gmail tools for direct access."""
        try:
            if self.service and self.toolkit:
                self.tools = {'send_message': GmailSendMessage(api_resource=self.service), 'search': GmailSearch(api_resource=self.service), 'get_message': GmailGetMessage(api_resource=self.service), 'get_thread': GmailGetThread(api_resource=self.service)}
                logging.info('Gmail tools initialized successfully')
        except Exception as e:
            logging.error(f'Failed to setup Gmail tools: {e}')

    @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
    def send_email(self, to: str, subject: str, body: str, body_type: str='html') -> dict:
        """
        Send an email using LangChain Gmail toolkit.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body content
            body_type: "html" or "plain" text format

        Returns:
            Dict with status and details
        """
        if not LANGCHAIN_GMAIL_AVAILABLE or not self.tools.get('send_message'):
            return {'status': 'error', 'message': 'LangChain Gmail toolkit not available'}
        try:
            if body_type == 'html':
                message_content = f'\n                To: {to}\n                Subject: {subject}\n                Content-Type: text/html; charset=utf-8\n\n                {body}\n                '
            else:
                message_content = f'\n                To: {to}\n                Subject: {subject}\n                Content-Type: text/plain; charset=utf-8\n\n                {body}\n                '
            send_tool = self.tools['send_message']
            result = send_tool.run(message_content)
            logging.info(f'Email sent successfully via LangChain: {result}')
            return {'status': 'success', 'message_id': str(result) if result else 'unknown', 'recipient': to, 'subject': subject, 'timestamp': datetime.now().isoformat(), 'method': 'langchain_gmail_toolkit'}
        except Exception as e:
            logging.error(f'Failed to send email via LangChain: {e}')
            return {'status': 'error', 'message': f'Failed to send email: {e!s}'}

    @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
    def search_messages(self, query: str, max_results: int=10) -> dict:
        """
        Search for messages using LangChain Gmail toolkit.

        Args:
            query: Gmail search query
            max_results: Maximum number of results to return

        Returns:
            Dict with search results
        """
        if not LANGCHAIN_GMAIL_AVAILABLE or not self.tools.get('search'):
            return {'status': 'error', 'message': 'LangChain Gmail toolkit not available'}
        try:
            search_tool = self.tools['search']
            search_query = f'{query} max:{max_results}'
            results = search_tool.run(search_query)
            return {'status': 'success', 'query': query, 'results': results, 'timestamp': datetime.now().isoformat()}
        except Exception as e:
            logging.error(f'Failed to search messages: {e}')
            return {'status': 'error', 'message': f'Search failed: {e!s}'}

    @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
    def get_message(self, message_id: str) -> dict:
        """
        Get a specific message using LangChain Gmail toolkit.

        Args:
            message_id: Gmail message ID

        Returns:
            Dict with message details
        """
        if not LANGCHAIN_GMAIL_AVAILABLE or not self.tools.get('get_message'):
            return {'status': 'error', 'message': 'LangChain Gmail toolkit not available'}
        try:
            get_tool = self.tools['get_message']
            message = get_tool.run(message_id)
            return {'status': 'success', 'message_id': message_id, 'message': message, 'timestamp': datetime.now().isoformat()}
        except Exception as e:
            logging.error(f'Failed to get message: {e}')
            return {'status': 'error', 'message': f'Failed to get message: {e!s}'}

    @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
    def get_thread(self, thread_id: str) -> dict:
        """
        Get a specific thread using LangChain Gmail toolkit.

        Args:
            thread_id: Gmail thread ID

        Returns:
            Dict with thread details
        """
        if not LANGCHAIN_GMAIL_AVAILABLE or not self.tools.get('get_thread'):
            return {'status': 'error', 'message': 'LangChain Gmail toolkit not available'}
        try:
            thread_tool = self.tools['get_thread']
            thread = thread_tool.run(thread_id)
            return {'status': 'success', 'thread_id': thread_id, 'thread': thread, 'timestamp': datetime.now().isoformat()}
        except Exception as e:
            logging.error(f'Failed to get thread: {e}')
            return {'status': 'error', 'message': f'Failed to get thread: {e!s}'}

    def get_available_tools(self) -> list[str]:
        """Get list of available LangChain Gmail tools."""
        if not LANGCHAIN_GMAIL_AVAILABLE:
            return []
        return list(self.tools.keys()) if self.tools else []

    def is_available(self) -> bool:
        """Check if LangChain Gmail toolkit is available and initialized."""
        return LANGCHAIN_GMAIL_AVAILABLE and self.service is not None and bool(self.tools)
gmail_manager = LangChainGmailManager()