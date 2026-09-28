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

from unittest.mock import MagicMock, patch

from economic_research.sub_agents.tools.search_skill import web_search_skill


def test_web_search_skill_match():
    """Test web search skill for a known mock query using mocked requests."""
    with patch("requests.post") as mock_post:
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "organic": [
                {
                    "title": "Found match for Austin",
                    "snippet": "Raleigh electricity rates",
                }
            ]
        }
        mock_post.return_value = mock_response

        # We set env var to bypass the check
        with patch("os.getenv", return_value="fake_key"):
            query = "Austin vs Raleigh"
            result = web_search_skill(query)
            assert "Results" in result
            assert "Austin" in result


def test_web_search_skill_generic():
    """Test web search skill for a generic query using mocked requests."""
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "organic": [
                {"title": "Detroit info", "snippet": "Unemployment stats"}
            ]
        }
        mock_post.return_value = mock_response

        with patch("os.getenv", return_value="fake_key"):
            query = "Detroit unemployment"
            result = web_search_skill(query)
            assert "Results" in result
            assert "Detroit" in result
