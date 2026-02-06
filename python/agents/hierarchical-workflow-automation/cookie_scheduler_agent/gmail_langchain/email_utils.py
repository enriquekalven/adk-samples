from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
'\nEmail utility functions using LangChain Gmail toolkit.\nThese functions provide convenient wrappers for agent integration.\n'
import logging
from .gmail_manager import gmail_manager

def send_confirmation_email_langchain(to: str, subject: str, body: str) -> dict:
    """
    Wrapper function for sending confirmation emails via LangChain Gmail toolkit.
    This function can be used directly in agent tools.

    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body content (HTML format)

    Returns:
        Dict with status and details
    """
    logging.info(f'LangChain Gmail: Sending confirmation email to {to}')
    return gmail_manager.send_email(to, subject, body, 'html')

def search_gmail_messages(query: str, max_results: int=10) -> dict:
    """
    Wrapper function for searching Gmail messages via LangChain.

    Args:
        query: Gmail search query
        max_results: Maximum number of results to return

    Returns:
        Dict with search results
    """
    logging.info(f'LangChain Gmail: Searching messages with query: {query}')
    return gmail_manager.search_messages(query, max_results)

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def get_gmail_message_details(message_id: str) -> dict:
    """
    Wrapper function for getting message details via LangChain.

    Args:
        message_id: Gmail message ID

    Returns:
        Dict with message details
    """
    logging.info(f'LangChain Gmail: Getting message details for {message_id}')
    return gmail_manager.get_message(message_id)

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def get_gmail_thread_details(thread_id: str) -> dict:
    """
    Wrapper function for getting thread details via LangChain.

    Args:
        thread_id: Gmail thread ID

    Returns:
        Dict with thread details
    """
    logging.info(f'LangChain Gmail: Getting thread details for {thread_id}')
    return gmail_manager.get_thread(thread_id)

def check_gmail_availability() -> bool:
    """
    Check if Gmail LangChain integration is available and ready.

    Returns:
        True if Gmail is available, False otherwise
    """
    return gmail_manager.is_available()

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def get_gmail_status() -> dict:
    """
    Get comprehensive status of Gmail LangChain integration.

    Returns:
        Dict with integration status details
    """
    return {'available': gmail_manager.is_available(), 'tools': gmail_manager.get_available_tools(), 'credentials_path': gmail_manager.credentials_file, 'token_path': gmail_manager.token_file}