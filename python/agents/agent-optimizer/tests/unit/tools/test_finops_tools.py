import os
import pytest
from agent_optimizer.tools.finops_tools import FinOpsAuditor, PivotAuditor, QualityClimber

@pytest.fixture
def temp_agent_file(tmp_path):
    """Creates a temporary agent file with some issues to audit."""
    content = """
from google.adk.apps.app import App

SYSTEM_INSTRUCTION = "This is a very long instruction that repeats in every request. " * 50
SUB_PROMPT = "Another redundant prompt. " * 20

app = App(name="test_app")
"""
    file_path = tmp_path / "test_agent.py"
    file_path.write_text(content)
    return str(file_path), str(tmp_path)

def test_finops_auditor_detects_issues(temp_agent_file):
    file_path, root_dir = temp_agent_file
    auditor = FinOpsAuditor(root_dir)
    results = auditor.run_optimizer_audit()
    
    # Check for token efficiency issues (large prompts)
    assert len(results["token_efficiency"]) >= 1
    assert any("SYSTEM_INSTRUCTION" in r["variable"] for r in results["token_efficiency"])
    
    # Check for caching opportunities (missing ContextCacheConfig)
    assert len(results["caching_opportunities"]) >= 1
    assert any("App" in r["issue"] for r in results["caching_opportunities"])

def test_pivot_auditor_returns_recommendations():
    auditor = PivotAuditor("/tmp")
    results = auditor.run_arch_review()
    
    assert results["status"] == "success"
    assert len(results["recommendations"]) > 0
    assert "FinOps Principal" in results["persona"]

def test_quality_climber_simulates_metrics():
    climber = QualityClimber("golden_set.json")
    results = climber.run_audit_deep()
    
    assert "metric" in results
    assert "Reasoning Density" in results["metric"]
    assert results["current_rd"] > 0
