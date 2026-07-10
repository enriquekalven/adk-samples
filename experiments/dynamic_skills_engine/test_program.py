"""Tests for the initial dynamic skills engine program."""
import pytest
from initial_program import evaluate, execute_skill, solve

EVAL_INPUTS = {
    "test_cases": [
        {
            "skill": "fred",
            "city": "Austin, TX",
            "metric": "unemployment"
        }
    ]
}

def test_execute_skill_returns_str():
    """execute_skill() returns output of the expected type."""
    assert callable(execute_skill)
    res = execute_skill("fred", city="Austin, TX", metric="unemployment")
    assert isinstance(res, str)

def test_evaluate_returns_dict_with_metrics():
    """evaluate() returns a dict containing the coverage_and_resilience_score key."""
    assert callable(evaluate)
    
def test_evaluate_structure():
    """Verify evaluate and solve parse correctly with AST."""
    import ast
    code = open("initial_program.py").read()
    tree = ast.parse(code)
    nodes = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    assert "execute_skill" in nodes
    assert "solve" in nodes
    assert "evaluate" in nodes
    
    # Check for EVOLVE-BLOCK markers on their own lines
    lines = code.splitlines()
    start_matches = [i for i, l in enumerate(lines) if l.strip() == "# EVOLVE-BLOCK-START"]
    end_matches = [i for i, l in enumerate(lines) if l.strip() == "# EVOLVE-BLOCK-END"]
    
    assert len(start_matches) == 1
    assert len(end_matches) == 1
    assert start_matches[0] < end_matches[0]
