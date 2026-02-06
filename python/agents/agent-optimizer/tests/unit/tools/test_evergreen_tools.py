# Copyright 2026 Google LLC
import sys
from unittest.mock import MagicMock, patch

# Mock bs4 before importing tools that use it
mock_bs4 = MagicMock()
sys.modules["bs4"] = mock_bs4

import pytest
from agent_optimizer.tools.evergreen_tools import load_technical_url, search_framework_docs

def test_search_framework_docs():
    """Tests formatting of search requests."""
    query = "memory management"
    frameworks = ["CrewAI", "LangGraph"]
    result = search_framework_docs(query, frameworks)
    assert "SEARCH_REQUEST: memory management for CrewAI, LangGraph" in result
    assert "Focus on official documentation" in result

def test_load_technical_url_success():
    """Tests successful loading and cleaning of a technical URL."""
    html_content = "<html><body><h1>Main Topic</h1><p>Some technical details here.</p></body></html>"
    mock_response = MagicMock()
    mock_response.text = html_content
    mock_response.raise_for_status.return_value = None
    
    mock_soup = MagicMock()
    # Simulate BeautifulSoup behavior
    mock_soup.get_text.return_value = "Main Topic\nSome technical details here."
    mock_bs4.BeautifulSoup.return_value = mock_soup
    
    with patch("requests.get", return_value=mock_response):
        result = load_technical_url("https://example.com/docs")
        assert "Main Topic" in result
        assert "Some technical details here." in result

def test_load_technical_url_error():
    """Tests error handling in loading URL."""
    with patch("requests.get", side_effect=Exception("Connection error")):
        result = load_technical_url("https://example.com/docs")
        assert "Error loading URL: Connection error" in result
