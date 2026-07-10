"""Evaluator for Evolved Dynamic Skills Adapter Engine.

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

EVALUATION_METRIC = "coverage_and_resilience_score"
EVALUATION_INPUTS = {
    "test_cases": [
        {
            "skill": "fred",
            "city": "Columbus, OH",
            "metric": "unemployment"
        },
        {
            "skill": "hud",
            "city": "Boise, ID",
            "metric": "fmr_2br"
        },
        {
            "skill": "trade",
            "state": "Idaho",
            "commodity": "Semiconductors"
        }
    ]
}


class EvaluationTimeout(Exception):
    pass


def _timeout_handler(signum, frame):
    raise EvaluationTimeout("Evaluation timed out")


if hasattr(signal, 'alarm'):
    signal.signal(signal.SIGALRM, _timeout_handler)


import re

def strict_solve(exec_namespace: dict[str, Any], eval_inputs: Mapping[str, Any]) -> dict[str, str]:
    """Applies the evolved engine to execute all requested test cases."""
    results = {}
    test_cases = eval_inputs.get("test_cases", [])
    execute_skill = exec_namespace.get("execute_skill")
    
    for tc in test_cases:
        skill = tc.get("skill", "")
        key_name = f"{skill}_{tc.get('city', tc.get('state', 'unknown'))}"
        
        try:
            output = execute_skill(skill, **tc)
            results[key_name] = output
        except Exception as e:
            results[key_name] = f"EXCEPTION: {e}"
            
    return results

def strict_evaluate(exec_namespace: dict[str, Any], eval_inputs: Mapping[str, Any]) -> dict[str, float]:
    """Scores the evolved DynamicSkillEngine based on strict execution coverage and true entity grounding."""
    try:
        outputs = strict_solve(exec_namespace, eval_inputs)
        
        s_coverage = 0.0
        s_resilience = 0.0
        
        test_cases = eval_inputs.get("test_cases", [])
        total_tests = len(test_cases)
        
        if total_tests == 0:
            return {"coverage_and_resilience_score": -10**12}
            
        for tc in test_cases:
            skill = tc.get("skill", "")
            entity = tc.get("city", tc.get("state", "unknown"))
            key_name = f"{skill}_{entity}"
            
            result = outputs.get(key_name, "")
            
            # Check for valid, non-error data extraction AND true entity grounding
            if result and "ERROR" not in result and "EXCEPTION" not in result and len(result) > 50:
                result_lower = result.lower()
                entity_clean = entity.split(',')[0].strip().lower()
                
                # Broaden to check for county fallbacks (e.g. Ada for Boise, Franklin for Columbus)
                entity_synonyms = {
                    "boise": ["boise", "ada", "16001"],
                    "columbus": ["columbus", "franklin", "39049"],
                    "idaho": ["idaho", "id"]
                }
                syns = entity_synonyms.get(entity_clean, [entity_clean])
                
                has_grounding = any(s in result_lower for s in syns)
                
                if has_grounding:
                    s_coverage += 1.0
                    
                    # Check for numerical data presence (indicating actual API hit, not fallback error strings)
                    has_num = bool(re.search(r'\d+', result))
                    has_dollar_or_pct = ('$' in result or '%' in result or '202' in result)
                    
                    if has_num and has_dollar_or_pct:
                        s_resilience += 1.0
                    
        # Calculate coverage ratio
        coverage_ratio = s_coverage / total_tests
        resilience_ratio = s_resilience / total_tests
        
        # Blended Score: 60% Coverage (does it return data?), 40% Resilience (is it real API numeric data?)
        composite = (0.60 * coverage_ratio * 10.0) + (0.40 * resilience_ratio * 10.0)
        
        logger.info(f"🧬 [Strict Evaluator] Result: Composite={composite:.2f} (Coverage={coverage_ratio*10:.1f}, Resilience={resilience_ratio*10:.1f})")
        
        if math.isnan(composite) or math.isinf(composite):
            return {"coverage_and_resilience_score": -10**12}
            
        return {
            "coverage_and_resilience_score": composite,
            "coverage_depth": coverage_ratio * 10.0,
            "api_resilience": resilience_ratio * 10.0
        }
        
    except Exception as e:
        logger.error(f"Top-level evaluation exception in SkillEngine: {e}")
        return {"coverage_and_resilience_score": -10**12}


def evaluate_program(
    code: str, timeout_seconds: int = 240,
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

            # Strict Override Gate
            result = strict_evaluate(exec_namespace, EVALUATION_INPUTS)


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
