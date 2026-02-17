import os
import pytest
from agent_optimizer.tools.finops_tools import FinOpsAuditor, PivotAuditor, QualityClimber

@pytest.fixture
def temp_agent_file(tmp_path):
    """Creates a temporary agent file with some issues to audit."""
    content = """
from google.adk import Agent
from google.adk.apps.app import App

SYSTEM_INSTRUCTION = "This is a very long instruction that repeats in every request. " * 50
SUB_PROMPT = "Another redundant prompt. " * 20

agent = Agent(name="test_agent", instruction=SYSTEM_INSTRUCTION)
app = App(root_agent=agent, name="test_app")
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

    # Check for Hive Mind (new in v2.0+)
    assert len(results["hive_mind_readiness"]) >= 1
    assert any("Semantic Caching" in r["issue"] for r in results["hive_mind_readiness"])

def test_pivot_auditor_returns_recommendations():
    auditor = PivotAuditor("/tmp")
    results = auditor.run_arch_review()
    
    assert results["status"] == "success"
    assert len(results["recommendations"]) > 0
    assert "Principal FinOps SME" in results["persona"]

def test_quality_climber_simulates_metrics():
    climber = QualityClimber("golden_set.json")
    results = climber.run_audit_deep()
    
    assert "metric" in results
    assert "Reasoning Density" in results["metric"]
    assert results["current_rd"] > 0

def test_context_visualizer():
    from agent_optimizer.tools.finops_tools import audit_context
    results = audit_context("/tmp")
    assert "visual_summary" in results
    assert "Heatmap" in results["visual_summary"]
    assert len(results["waste_segments"]) > 0
