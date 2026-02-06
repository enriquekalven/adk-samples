# Copyright 2026 Google LLC
import pytest
from google.adk import Agent
from google.adk.apps.app import App
from agent_optimizer.agent import agent_optimizer, app
from agent_optimizer.prompts import STATIC_INSTRUCTION, INSTRUCTION

def test_agent_optimizer_config():
    """Tests that the agent is initialized with the correct parameters."""
    assert agent_optimizer.name == "AgentOptimizer"
    assert agent_optimizer.model == "gemini-2.5-flash"
    assert agent_optimizer.static_instruction == STATIC_INSTRUCTION
    assert agent_optimizer.instruction == INSTRUCTION
    assert agent_optimizer.planner is not None
    assert len(agent_optimizer.tools) > 0

def test_app_config():
    """Tests that the app is initialized with the correct production configs."""
    assert app.name == "agent_optimizer_app"
    assert app.root_agent == agent_optimizer
    assert app.context_cache_config is not None
    assert app.context_cache_config.min_tokens == 2048
    assert app.resumability_config.is_resumable is True
    assert app.events_compaction_config is not None
    assert app.events_compaction_config.compaction_interval == 10
