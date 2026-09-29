# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Entrypoint and packaging checks for `make mcp`, eval, `make run`, deploy."""

import asyncio
import re
import tomllib
from pathlib import Path
from unittest.mock import MagicMock, patch

RECIPE_ROOT = Path(__file__).resolve().parents[2]


def _normalize(requirement: str) -> str:
    return re.sub(r"\s+", "", requirement).lower()


def test_mcp_server_imports_and_registers_tools():
    """`make mcp` broke when mcp 2.x removed mcp.server.fastmcp."""
    import mcp_server

    tools = asyncio.run(mcp_server.mcp.list_tools())
    names = {tool.name for tool in tools}
    assert {"get_macro_stats", "get_labor_series", "get_tax_rates"} <= names


def test_eval_script_imports(monkeypatch):
    """eval/run_eval.py needs the google-cloud-aiplatform[evaluation] extra."""
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
    with (
        patch("google.auth.default", return_value=(MagicMock(), "test")),
        patch("vertexai.init"),
    ):
        from eval import run_eval

    assert callable(run_eval.run_benchmarks)


def test_cli_main_exits_cleanly_on_eof(monkeypatch, capsys):
    """`make run` used to import the agent and exit without a prompt."""
    # Note: `from economic_research import agent` yields the exported App
    # (the package __init__ rebinds `agent`), so import from the module path.
    from economic_research.agent import main

    monkeypatch.setattr("builtins.input", MagicMock(side_effect=EOFError))
    main()

    assert "Economic Research Agent" in capsys.readouterr().out


def test_requirements_txt_matches_pyproject():
    """deploy.py ships requirements.txt to Agent Engine; it must not drift.

    It used to be missing statsmodels/mcp/markdown, so the deployed agent
    failed on import.
    """
    pyproject = tomllib.loads((RECIPE_ROOT / "pyproject.toml").read_text())
    expected = {_normalize(d) for d in pyproject["project"]["dependencies"]}
    lines = (RECIPE_ROOT / "requirements.txt").read_text().splitlines()
    actual = {
        _normalize(line)
        for line in lines
        if line.strip() and not line.lstrip().startswith("#")
    }
    assert actual == expected


def test_makefile_targets_reference_existing_files():
    makefile = (RECIPE_ROOT / "Makefile").read_text()
    for script in re.findall(
        r"uv run (?:python3?|streamlit run) (\S+\.py)", makefile
    ):
        assert (RECIPE_ROOT / script).exists(), f"Makefile references {script}"
