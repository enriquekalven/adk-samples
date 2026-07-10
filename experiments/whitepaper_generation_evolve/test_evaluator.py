"""Tests for the evaluator."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import pytest

from evaluator import evaluate_program

def test_evaluate_program_returns_score_and_insights():
    """evaluate_program() returns a dict with score and insights."""
    # Since running the FULL evaluate_program will call Gemini, we can verify that the evaluator
    # accepts the code, executes it, and handles the flow.
    # We can provide a mocked evaluate function that doesn't call Gemini to test evaluator.py itself!
    mock_code = """
def solve(eval_inputs):
    return "This is a mock whitepaper. # Executive Summary # Methodology # Data Analysis |---|---|"

def evaluate(eval_inputs):
    return {
        "composite_quality_score": 8.5,
        "narrative_professionalism": 9.0,
        "data_grounding_rigor": 8.0,
        "synthesis_correlations": 8.0,
        "citation_compliance": 9.0
    }
"""
    result = evaluate_program(mock_code)
    assert "scores" in result or "score" in result
    if "scores" in result:
        assert isinstance(result["scores"], list)
        assert result["scores"][0]["metric"] == "composite_quality_score"
        assert result["scores"][0]["score"] == 8.5
    else:
        assert result["score"] == 8.5
    assert isinstance(result["insights"], list)

def test_evaluate_program_returns_error_insights_on_failure():
    """evaluate_program() returns error insights for bad code."""
    result = evaluate_program("def !!!")
    assert "scores" not in result or result.get("score") is None
    labels = {i["label"] for i in result.get("insights", [])}
    assert "error" in labels
    assert "traceback" in labels

def test_cli_main_writes_output_file():
    """main() writes a valid JSON output file."""
    tmpdir = tempfile.mkdtemp()
    try:
        mock_code = """
def solve(eval_inputs):
    return "Mock report"

def evaluate(eval_inputs):
    return {"composite_quality_score": 7.0}
"""
        initial_file = os.path.join(tmpdir, "initial_program.py")
        with open(initial_file, "w") as f:
            f.write(mock_code)
            
        shutil.copy("evaluator.py", os.path.join(tmpdir, "evaluator.py"))
        output_file = os.path.join(tmpdir, "scores.json")

        cmd = [sys.executable, "evaluator.py",
               "--output-file", output_file,
               "--program-dir", tmpdir]

        result = subprocess.run(
            cmd,
            cwd=tmpdir, capture_output=True, text=True, timeout=30,
            check=False,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

        with open(output_file) as f:
            data = json.load(f)
            
        assert "scores" in data or "score" in data
        assert "insights" in data
    finally:
        shutil.rmtree(tmpdir)
