# Copyright 2026 Google LLC
import os
import pytest
from unittest.mock import patch, mock_open
from agent_optimizer.tools.analysis_tools import (
    read_agent_file,
    list_agent_directory,
    get_token_counts,
    analyze_resource_efficiency
)

def test_read_agent_file():
    """Tests reading an agent file."""
    content = "print('hello')"
    with patch("builtins.open", mock_open(read_data=content)):
        result = read_agent_file("/fake/path.py")
        assert result == content

def test_list_agent_directory():
    """Tests listing files in a directory."""
    with patch("os.listdir") as mock_listdir, \
         patch("os.path.isfile") as mock_isfile:
        mock_listdir.return_value = ["file1.py", "subdir"]
        mock_isfile.side_effect = lambda x: x.endswith(".py")
        
        result = list_agent_directory("/fake/dir")
        assert result == ["file1.py"]

def test_get_token_counts():
    """Tests token count and cost estimation."""
    text = "This is a test sentence." # 24 chars
    result = get_token_counts(text)
    assert result["token_estimate"] == 6 # 24 / 4
    assert "estimated_cost_usd" in result
    assert result["latency_impact"] == "⚡ Ultra-Low (<200ms)"

def test_analyze_resource_efficiency_adk():
    """Tests efficiency analysis for ADK snippets."""
    code = "agent = Agent(name='test')"
    result = analyze_resource_efficiency("ADK", code)
    assert result["cost_efficiency"] == "Sub-optimal"
    assert any("ContextCacheConfig" in tip for tip in result["optimization_tips"])

def test_analyze_resource_efficiency_langgraph():
    """Tests efficiency analysis for LangGraph snippets."""
    code = "graph = StateGraph(State)"
    result = analyze_resource_efficiency("LangGraph", code)
    assert result["memory_risk"] == "High"
    assert any("checkpointer" in tip.lower() for tip in result["optimization_tips"])

def test_analyze_resource_efficiency_crewai():
    """Tests efficiency analysis for CrewAI snippets."""
    code = "crew = Crew(process=Process.sequential)"
    result = analyze_resource_efficiency("CrewAI", code)
    assert any("sequential" in b.lower() for b in result["potential_bottlenecks"])
