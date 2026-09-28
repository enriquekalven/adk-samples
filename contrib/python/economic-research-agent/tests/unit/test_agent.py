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

import os

from economic_research.agent import get_session_api_key, set_session_api_key


def test_set_session_api_key_valid(monkeypatch):
    key_name = "FRED_API_KEY"
    key_value = "test_value"
    monkeypatch.delenv(key_name, raising=False)

    result = set_session_api_key(key_name, key_value)

    assert "Successfully set" in result
    assert get_session_api_key(key_name) == key_value
    assert os.environ.get(key_name) is None


def test_set_session_api_key_invalid():
    key_name = "INVALID_KEY"
    key_value = "test_value"

    result = set_session_api_key(key_name, key_value)

    assert "ERROR" in result
    assert get_session_api_key(key_name) is None
    assert os.environ.get(key_name) is None
