from tenacity import retry, wait_exponential, stop_after_attempt
import logging
import requests
logger = logging.getLogger(__name__)

def search_framework_docs(query: str, frameworks: list[str] | None=None) -> str:
    """Searches for the latest documentation and best practices for specific AI frameworks.

    Args:
        query (str): The search query (e.g., 'CrewAI memory management best practices').
        frameworks (list[str] | None): Optional list of frameworks to focus on (e.g. ['CrewAI', 'LangGraph']).

    Returns:
        str: A summary of search results.
    """
    framework_context = f" for {', '.join(frameworks)}" if frameworks else ''
    return f'SEARCH_REQUEST: {query}{framework_context}. Focus on official documentation, GitHub repos, and high-quality technical blogs (Medium, Dev.to).'

def load_technical_url(url: str) -> str:
    """Reads and cleans the content of a technical documentation URL.

    Args:
        url (str): The absolute URL to the documentation page.

    Returns:
        str: The cleaned text content of the page or an error message.
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, timeout=15, headers=headers)
        response.raise_for_status()
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        for script_or_style in soup(['script', 'style', 'header', 'footer', 'nav']):
            script_or_style.decompose()
        text = soup.get_text(separator='\n')
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split('  '))
        text = '\n'.join((chunk for chunk in chunks if chunk))
        return text[:15000]
    except Exception as e:
        return f'Error loading URL: {e!s}'