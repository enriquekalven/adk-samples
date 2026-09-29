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

"""FRED client with a network timeout.

``fredapi.Fred`` calls ``urlopen(url)`` with no timeout, so one stalled
request can hang a tool (and, because tools run on the event loop, every
session) indefinitely. ``TimeoutFred`` overrides the private fetch method to
pass a timeout. Error messages never include the request URL, which carries
the API key.
"""

import os
import xml.etree.ElementTree as ET

import requests
from fredapi import Fred

from economic_research.shared_libraries.helper import (
    HTTP_TIMEOUT_SECONDS,
    get_session_api_key,
)


class TimeoutFred(Fred):
    """``fredapi.Fred`` with a per-request timeout."""

    def __init__(self, *args, timeout: float = HTTP_TIMEOUT_SECONDS, **kwargs):
        super().__init__(*args, **kwargs)
        self.timeout = timeout

    # Overrides the name-mangled ``Fred.__fetch_data``.
    def _Fred__fetch_data(self, url):
        if not url.startswith("https://"):
            raise ValueError("FRED URLs must use https")
        response = requests.get(
            url, params={"api_key": self.api_key}, timeout=self.timeout
        )
        if response.status_code != 200:
            try:
                message = _parse_xml(response.content).get("message")
            except ET.ParseError:
                message = None
            raise ValueError(
                message or f"FRED request failed (HTTP {response.status_code})"
            )
        return _parse_xml(response.content)


def _parse_xml(payload: bytes) -> ET.Element:
    # Same parser fredapi uses; the payload comes from the fixed FRED https
    # endpoint, not from user input.
    return ET.fromstring(payload)  # noqa: S314


def get_fred_client() -> TimeoutFred | None:
    """Returns a FRED client, or None when no usable API key is configured."""
    fred_key = get_session_api_key("FRED_API_KEY", os.getenv("FRED_API_KEY"))
    if not fred_key:
        return None
    try:
        return TimeoutFred(api_key=fred_key)
    except ValueError:
        return None
