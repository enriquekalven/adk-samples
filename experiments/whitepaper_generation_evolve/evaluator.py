"""Evaluator for Deep Research Whitepaper Generation Orchestrator.

CLI-compatible evaluator for use with the ae CLI.
The ae CLI invokes this as:
  python evaluator.py --output-file <path> --program-dir <workspace>
"""

import argparse
import contextlib
import io
import json
import logging
import math
import os
import signal
import sys
import traceback
from typing import Any, Mapping

import numpy as np

logger = logging.getLogger(__name__)

EVALUATION_METRIC = "composite_quality_score"
EVALUATION_INPUTS = {
    "research_topic": "Compare the Real GDP growth rate, industrial electricity rates, and workforce AI exposure risk for a new tech and manufacturing hub between Austin, TX and Columbus, OH."
}


class EvaluationTimeout(Exception):
    pass


def _timeout_handler(signum, frame):
    raise EvaluationTimeout("Evaluation timed out")


if hasattr(signal, 'alarm'):
    signal.signal(signal.SIGALRM, _timeout_handler)


def evaluate_program(
    code: str, timeout_seconds: int = 600,
) -> dict[str, Any]:
    """Execute candidate code and return the evaluation result.

    Returns:
        {"scores": [{"metric": str, "score": float}, ...], "insights": [...]}
    """
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    try:
        if hasattr(signal, 'alarm'):
            signal.alarm(timeout_seconds)
            
        exec_namespace: dict[str, Any] = {
            "Any": Any,
            "Mapping": Mapping,
        }

        with contextlib.redirect_stdout(stdout_capture), \
             contextlib.redirect_stderr(stderr_capture):
            exec(code, exec_namespace)
            eval_func = exec_namespace.get("evaluate")

            if callable(eval_func):
                result = eval_func(EVALUATION_INPUTS)
            else:
                return _failure(
                    "Program missing callable 'evaluate' function",
                    stdout=stdout_capture.getvalue(),
                    stderr=stderr_capture.getvalue(),
                )

        raw_score = result.get(EVALUATION_METRIC)
        stdout = stdout_capture.getvalue()
        stderr = stderr_capture.getvalue()

        if raw_score is not None and raw_score != -np.inf and raw_score > -1e11:
            insights = []
            if stdout:
                insights.append({"label": "stdout", "text": stdout})
            if stderr:
                insights.append({"label": "stderr", "text": stderr})
                
            # Log individual objectives into insights for LLM visibility
            for k, v in result.items():
                if k != EVALUATION_METRIC:
                    insights.append({"label": k, "text": str(v)})

            # Construct Multi-Metric JSON response payload
            # The FIRST score in the array is the PRIMARY optimization target
            scores_array = [
                {"metric": EVALUATION_METRIC, "score": float(raw_score)}
            ]
            for k, v in result.items():
                if k != EVALUATION_METRIC and isinstance(v, (int, float)):
                    scores_array.append({"metric": k, "score": float(v)})
                    
            return {
                "scores": scores_array,
                "insights": insights
            }

        return _failure(
            f"Metric '{EVALUATION_METRIC}' invalid: {raw_score}",
            stdout=stdout, stderr=stderr,
        )

    except EvaluationTimeout:
        return _failure(
            f"Timed out after {timeout_seconds}s",
            tb=traceback.format_exc(),
            stdout=stdout_capture.getvalue(),
            stderr=stderr_capture.getvalue(),
        )
    except Exception as e:
        return _failure(
            f"Evaluation failed: {e}",
            tb=traceback.format_exc(),
            stdout=stdout_capture.getvalue(),
            stderr=stderr_capture.getvalue(),
        )
    finally:
        if hasattr(signal, 'alarm'):
            signal.alarm(0)


def _failure(error, tb=None, stdout="", stderr=""):
    """Build a failure result with insights."""
    insights = [{"label": "error", "text": error}]
    if tb:
        insights.append({"label": "traceback", "text": tb})
    if stdout:
        insights.append({"label": "stdout", "text": stdout})
    if stderr:
        insights.append({"label": "stderr", "text": stderr})
    return {"score": None, "insights": insights}


def main():
    """CLI entry point. Called by the ae CLI as:
      python evaluator.py --output-file <path> --program-dir <workspace>
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-file", required=True)
    parser.add_argument("--program-dir", required=True)
    args = parser.parse_args()

    # Add program dir to sys.path so flat imports resolve.
    sys.path.insert(0, args.program_dir)

    program_path = os.path.join(args.program_dir, "initial_program.py")
    with open(program_path) as f:
        code = f.read()

    result = evaluate_program(code)

    with open(args.output_file, "w") as f:
        json.dump(result, f, indent=2)


if __name__ == "__main__":
    main()
