import os
import pytest
from agent_optimizer.tools.remediator import CodeRemediator

@pytest.fixture
def agent_file_to_fix(tmp_path):
    """Creates an agent file that needs remediation."""
    content = """
from google.adk.apps.app import App

def call_llm(query):
    # This function needs a retry decorator
    pass

app = App(name="legacy_app")
"""
    file_path = tmp_path / "legacy_agent.py"
    file_path.write_text(content)
    return str(file_path), str(tmp_path)

def test_code_remediator_applies_fixes(agent_file_to_fix):
    file_path, root_dir = agent_file_to_fix
    remediator = CodeRemediator(root_dir)
    fixed_files = remediator.apply_fixes()
    
    assert file_path in fixed_files
    
    with open(file_path, "r") as f:
        new_content = f.read()
    
    # Check if ContextCacheConfig was injected
    assert "ContextCacheConfig" in new_content
    # Check if EventsCompactionConfig was injected
    assert "EventsCompactionConfig" in new_content
    # Check if @retry was injected
    assert "@retry" in new_content
    # Check if imports were added
    assert "from tenacity import retry" in new_content
    assert "from google.adk.agents.context_cache_config import ContextCacheConfig" in new_content

def test_remediator_skips_fixed_files(tmp_path):
    """Ensure it doesn't double-remediate."""
    content = """
from tenacity import retry
@retry
def call_llm(): pass
"""
    file_path = tmp_path / "fixed_agent.py"
    file_path.write_text(content)
    
    remediator = CodeRemediator(str(tmp_path))
    fixed_files = remediator.apply_fixes()
    
    assert len(fixed_files) == 0
