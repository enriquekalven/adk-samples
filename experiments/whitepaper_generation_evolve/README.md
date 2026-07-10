# Deep Research Whitepaper Generation Orchestrator
**Objective**: Optimize the Economic Research Agent to produce high-end, grounded, Deep Research consulting whitepapers dynamically.

## Included Files
* `initial_program.py`: Contains the `solve()` and `evaluate()` functions. Target for evolution inside `# EVOLVE-BLOCK-START`.
* `evaluator.py`: Standalone CLI evaluator called by the `ae` CLI.
* `problem_description.md`: Detailed problem constraints and objectives sent to the LLM.
* `test_program.py`: Pytest suite verifying the initial program's structure and contracts.
* `test_evaluator.py`: Pytest suite for `evaluator.py`.
* `pyproject.toml`: The `uv` configuration file managing the dependency virtual environment.

## Running Tests
Ensure you are in the experiment directory and run:
```bash
uv run pytest -v
```

## Launching with AlphaEvolve
To launch this experiment on the GCP backend using the `ae` CLI:
```bash
ae experiment start whitepaper_orchestrator \
  --program-dir . \
  --evaluator evaluator.py \
  --description "Evolve multi-step deep research whitepaper synthesis"
```
Or simply instruct your **AlphaEvolve Orchestrator** sub-agent to transition to Phase 2 (Runner)!
