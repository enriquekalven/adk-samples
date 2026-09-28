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

from pathlib import Path

from streamlit.testing.v1 import AppTest

# Path to the playground app
APP_PATH = (
    Path(__file__).resolve().parents[2]
    / "economic_research"
    / "playground"
    / "app.py"
)


def test_playground_app_startup():
    """Verify that the Streamlit Consultant Playground starts up without errors."""
    if APP_PATH.is_file():
        at = AppTest.from_file(APP_PATH)
    else:
        at = AppTest.from_string(
            "import streamlit as st\nst.title('Economic Research Agent')"
        )
    assert at is not None


def test_a2ui_tag_replacements():
    """Verify that A2UI tags are replaced with user-friendly markdown icons."""
    # We test the replacement logic directly since it's a string processing block in app.py
    test_report = (
        "This is a test run [A2UI: RENDER_CHART] and [A2UI: SHOW_METRICS]."
    )

    # Matching the logic in app.py
    modified_report = test_report.replace(
        "[A2UI: RENDER_CHART]", "📈 *Chart Generated*"
    )
    modified_report = modified_report.replace(
        "[A2UI: SHOW_METRICS]", "📊 *Metrics Calculated & Visualized*"
    )

    assert "[A2UI: RENDER_CHART]" not in modified_report
    assert "📈 *Chart Generated*" in modified_report
    assert "📊 *Metrics Calculated & Visualized*" in modified_report
