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
    mock_code = """
def execute_skill(skill_name, **kwargs):
    return "Sample extracted data 123% in 2026."

def evaluate(eval_inputs):
    return {
        "coverage_and_resilience_score": 8.5,
        "coverage_depth": 9.0,
        "api_resilience": 8.0
    }
"""
    result = evaluate_program(mock_code)
    assert "scores" in result or "score" in result
    assert isinstance(result.get("scores", result.get("score")), (list, float))
    assert isinstance(result["insights"], list)

def test_cli_main_writes_output_file():
    """main() writes a valid JSON output file."""
    tmpdir = tempfile.mkdtemp()
    try:
        mock_code = """
def execute_skill(skill_name, **kwargs):
    return "Mock"

def evaluate(eval_inputs):
    return {"coverage_and_resilience_score": 7.0}
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
