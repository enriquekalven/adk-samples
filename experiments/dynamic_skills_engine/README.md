# Evolved Dynamic Skills Adapter Engine
**Objective**: Evolve the 29 economic tools from rigid heuristics into a robust, self-expanding coverage library dynamically.

## Included Files
* `initial_program.py`: Contains the `execute_skill()`, `solve()`, and `evaluate()` functions. Target for evolution inside `# EVOLVE-BLOCK-START`.
* `evaluator.py`: Standalone CLI evaluator called by the `ae` CLI.
* `problem_description.md`: Detailed problem constraints and objectives.
* `test_program.py`: Pytest suite verifying the initial program's structure.
* `test_evaluator.py`: Pytest suite for `evaluator.py`.
* `pyproject.toml`: The `uv` configuration file.

## Running Tests
```bash
uv run pytest -v
```

## Launching with AlphaEvolve
```bash
ae experiment start dynamic_skills_engine \
  --program-dir . \
  --evaluator evaluator.py \
  --description "Evolve dynamic FIPS/MSA/HS-Code coverage for all 29 tools"
```
Or instruct the **AlphaEvolve Orchestrator** to transition to Phase 2 (Runner)!
