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

"""ADK Skill: Real-Time Market Sentiment (NewsAPI)."""

import json
import logging
import os

import requests
from pydantic import BaseModel, Field

from economic_research.shared_libraries.helper import (
    HTTP_TIMEOUT_SECONDS,
    get_session_api_key,
    redact_secrets,
    safe_error,
)

logger = logging.getLogger(__name__)

NEWS_API_URL = "https://newsapi.org/v2/everything"
_MAX_ERROR_BODY_CHARS = 300


class SentimentRequest(BaseModel):
    query: str = Field(
        ...,
        description="Query to search for news sentiment (e.g. 'Austin labor market' or 'Raleigh economic growth').",
    )
    language: str = Field("en", description="Language for news search.")


def analyze_market_sentiment(query: str, language: str = "en") -> str:
    """
    Fetches real-time news headlines to perform sentiment analysis on MSAs and industries.
    Use this to catch 'Soft Signals' (strikes, recent large relocations, political decisions)
    that government data (BLS/Census) might have missed.
    """
    api_key = get_session_api_key("NEWS_API_KEY", os.getenv("NEWS_API_KEY"))
    if not api_key:
        return "ERROR: NEWS_API_KEY is not set in environment variables."

    # NewsAPI endpoint for top headlines or everything.
    # 'everything' allows for more specific query matching.
    # Passing params (instead of an f-string URL) URL-encodes the query.
    params = {
        "q": query,
        "language": language,
        "sortBy": "relevancy",
        "pageSize": 8,
        "apiKey": api_key,
    }

    try:
        response = requests.get(
            NEWS_API_URL, params=params, timeout=HTTP_TIMEOUT_SECONDS
        )
        if response.status_code == 200:
            data = response.json()
            articles = data.get("articles", [])

            if not articles:
                return f"No recent news found for query: {query}."

            results = []
            for art in articles:
                results.append(
                    {
                        "Title": art["title"],
                        "Source": art["source"]["name"],
                        "PublishedAt": art["publishedAt"],
                        "Description": art["description"][:150] + "..."
                        if art["description"]
                        else "N/A",
                    }
                )

            # The Scribe node or LLM will perform the final sentiment weighting on these results.
            return json.dumps(results, indent=2)
        else:
            body = redact_secrets(str(response.text))[:_MAX_ERROR_BODY_CHARS]
            return f"Error from NewsAPI: {response.status_code} - {body}"

    except Exception as e:
        logger.warning("NewsAPI request failed: %s", safe_error(e))
        return f"Request failed: {safe_error(e)}"
