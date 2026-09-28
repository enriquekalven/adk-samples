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

import requests

from economic_research.shared_libraries.helper import get_session_api_key


def web_search_skill(query: str) -> str:
    """
    Live web search using Serper.dev API.
    Ensure SERPER_API_KEY is defined in your environment or .env file.
    """
    serper_key = get_session_api_key(
        "SERPER_API_KEY", os.getenv("SERPER_API_KEY")
    )
    if not serper_key:
        return "⚠️ Error: SERPER_API_KEY not found in environment. Please add it to your .env file."

    url = "https://google.serper.dev/search"
    payload = {"q": query}
    headers = {"X-API-KEY": serper_key, "Content-Type": "application/json"}

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        if response.status_code == 200:
            results = response.json().get("organic", [])
            if not results:
                return f"[Serper] No organic results found for '{query}'."
            summaries = [
                f"- {res.get('title')}: {res.get('snippet')}"
                for res in results[:3]
            ]
            return "### 🔍 Live Google Search Results (Serper):\n" + "\n".join(
                summaries
            )
        return f"[Serper Error] Failed to fetch search results. HTTP Status {response.status_code}."
    except Exception as e:
        return f"[Serper Request Failed] {e}"
