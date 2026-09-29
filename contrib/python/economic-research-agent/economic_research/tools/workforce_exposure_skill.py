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

"""Workforce & AI Task Exposure Analysis Skill."""

import json
import logging
import os
import re
from typing import Any

import requests
from google import genai
from google.genai import types

from economic_research.shared_libraries.helper import (
    HTTP_TIMEOUT_SECONDS,
    SANDBOX_SOURCE,
    get_default_model,
    get_session_api_key,
    safe_error,
)

logger = logging.getLogger(__name__)

ONET_SOURCE = "O*NET Web Services (task list)"
GEMINI_ESTIMATE_SOURCE = (
    f"{ONET_SOURCE} + Gemini exposure classification (model estimate)"
)
CLASSIFICATION_FAILED_SOURCE = (
    f"{ONET_SOURCE}; exposure classification unavailable (no estimate)"
)
CURATED_ESTIMATE_SOURCE = (
    f"{SANDBOX_SOURCE}: curated estimate based on O*NET task classifications "
    "and AI labor exposure studies"
)


def classify_onet_tasks_with_gemini(title: str, tasks: list[str]) -> dict:
    """Classifies O*NET occupational tasks using Vertex AI / Gemini.

    On failure the returned dict has ``classification_failed=True`` and
    "Unknown" exposure fields; it never invents an exposure rating.
    """
    try:
        # Load GCP project metadata from environment
        project = os.getenv("GCP_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT")
        location = os.getenv("GCP_LOCATION")

        client = genai.Client(vertexai=True, project=project, location=location)
        prompt = f"""
        Analyze the AI exposure and automation potential for the occupation: "{title}".
        Below is the official task list for this role:
        
        {json.dumps(tasks, indent=2)}
        
        Compute the following analysis:
        1. "exposure_level": Rate as High, Medium-High, Medium, Medium-Low, or Low.
        2. "impact_mode": Classify the primary mode, e.g. "Automation (Directive Workflows)", "Augmentation (Task Iteration & Validation)", "Minimal Impact", etc.
        3. "complexity_score": E.g. "High (16+ years education required)", "Medium (12-14 years education required)".
        4. "key_exposed_tasks": Identify the top 3 most exposed/impacted tasks from the list above.
        5. "recommendation": Provide a strategic consulting recommendation for organizations employing this role.
        
        Format your response as a valid JSON object with the keys:
        - exposure_level
        - impact_mode
        - complexity_score
        - key_exposed_tasks (list of strings)
        - recommendation (string)
        
        Do not include markdown code block formatting or explanations. Return only the raw JSON.
        """

        response = client.models.generate_content(
            model=get_default_model(),
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            ),
        )
        parsed = json.loads(response.text)
        if not isinstance(parsed, dict):
            raise ValueError("Gemini returned a non-object JSON payload.")
        return parsed
    except Exception as e:
        logger.warning("Gemini task analysis failed: %s", safe_error(e))
        return {
            "exposure_level": "Unknown (classification unavailable)",
            "impact_mode": "Unknown",
            "complexity_score": "Requires manual review",
            "key_exposed_tasks": tasks[:3] if tasks else ["N/A"],
            "recommendation": (
                "Automated classification failed "
                f"({safe_error(e)}); review the O*NET task list manually."
            ),
            "classification_failed": True,
        }


def _match_exposure_db(occ_lower: str, exposure_db: dict) -> dict | None:
    """Exact match first, then whole-word phrase match in either direction.

    Plain substring matching is avoided: an empty string (or a stray letter)
    is a substring of every key and would silently return the first entry.
    """
    if not occ_lower:
        return None
    if occ_lower in exposure_db:
        return exposure_db[occ_lower]
    for key, val in exposure_db.items():
        if re.search(rf"\b{re.escape(key)}\b", occ_lower) or re.search(
            rf"\b{re.escape(occ_lower)}\b", key
        ):
            return val
    return None


def analyze_workforce_exposure(occupations: list[str]) -> str:
    """
    Analyzes AI exposure (automation vs. augmentation) and strategic recommendations
    for a list of occupational domains or standard job titles.

    Args:
        occupations: List of standard occupational categories or job titles
                    (e.g., ["Software Developers", "Customer Service Representatives", "Financial Analysts", "Retail Sales"]).

    Returns:
        JSON string containing the AI exposure scores, primary impact mode, and strategic action plans.
    """
    # Grounded mapping based on O*NET task classifications and AI labor exposure studies
    exposure_db = {
        "software developers": {
            "soc": "15-1252",
            "exposure_level": "High",
            "impact_mode": "Augmentation (Task Iteration & Validation)",
            "complexity_score": "High (16+ years education required)",
            "key_exposed_tasks": [
                "Writing/refactoring code",
                "System design integration",
                "Unit testing and debugging",
            ],
            "recommendation": "High opportunity for productivity gain. Shift developer hours toward architectural design and system safety.",
        },
        "computer and mathematical": {
            "soc": "15-0000",
            "exposure_level": "High",
            "impact_mode": "Augmentation (Task Iteration & Validation)",
            "complexity_score": "High (16+ years education required)",
            "key_exposed_tasks": [
                "Data analysis",
                "Statistical modeling",
                "Algorithmic engineering",
            ],
            "recommendation": "Upskill teams on context caching and collaborative agent programming to accelerate output.",
        },
        "customer service representatives": {
            "soc": "43-4051",
            "exposure_level": "High",
            "impact_mode": "Automation (Directive Workflows)",
            "complexity_score": "Medium (12-14 years education required)",
            "key_exposed_tasks": [
                "Answering billing inquiries",
                "Resolving standard order complaints",
                "Ticket routing",
            ],
            "recommendation": "High displacement risk. Automate repetitive tier-1 ticketing via API agents; transition human agents to high-empathy case management.",
        },
        "office and administrative support": {
            "soc": "43-0000",
            "exposure_level": "High",
            "impact_mode": "Automation (Directive Workflows)",
            "complexity_score": "Medium (12-14 years education required)",
            "key_exposed_tasks": [
                "Data entry",
                "Meeting scheduling",
                "Document formatting",
            ],
            "recommendation": "Incorporate document-extraction and RAG agents to automate office pipelines.",
        },
        "financial analysts": {
            "soc": "13-2051",
            "exposure_level": "Medium-High",
            "impact_mode": "Augmentation (Validation & Learning)",
            "complexity_score": "High (16+ years education required)",
            "key_exposed_tasks": [
                "Corporate financial modeling",
                "Market trend analysis",
                "Investment memo preparation",
            ],
            "recommendation": "Utilize agents for rapid macro-data ingestion (FRED/Census); focus analyst time on risk-assessment and narrative synthesis.",
        },
        "management": {
            "soc": "11-0000",
            "exposure_level": "Medium",
            "impact_mode": "Augmentation (Feedback Loops)",
            "complexity_score": "High (16+ years education required)",
            "key_exposed_tasks": [
                "Strategic decision making",
                "Team performance reviews",
                "Inter-department coordination",
            ],
            "recommendation": "Low displacement risk. Deploy conversational dashboards to accelerate executive context-gathering.",
        },
        "tutors": {
            "soc": "25-3000",
            "exposure_level": "Medium",
            "impact_mode": "Augmentation (Learning & Feedback)",
            "complexity_score": "Medium-High (14-16 years education required)",
            "key_exposed_tasks": [
                "Grading assignments",
                "Curriculum pacing",
                "Explaining core subjects",
            ],
            "recommendation": "Leverage AI for personalized student pacing and automated grading support; focus human time on mentoring.",
        },
        "retail sales": {
            "soc": "41-2031",
            "exposure_level": "Low",
            "impact_mode": "Minimal Impact",
            "complexity_score": "Low (12 years education required)",
            "key_exposed_tasks": [
                "Processing local payments",
                "Stocking inventory",
                "In-person product advice",
            ],
            "recommendation": "Low overall exposure. Focus AI investment on logistics and back-office supply chains rather than consumer interaction.",
        },
    }

    if not isinstance(occupations, list) or not any(
        isinstance(occ, str) and occ.strip() for occ in occupations
    ):
        return json.dumps(
            {
                "ERROR": (
                    "Provide at least one non-empty occupation title "
                    "(e.g. 'Software Developers')."
                )
            },
            indent=2,
        )

    results: list[dict[str, Any]] = []
    api_key = (get_session_api_key("ONET_API_KEY") or "").strip()
    headers = (
        {"accept": "application/json", "X-API-Key": api_key}
        if api_key
        else None
    )

    for occ in occupations:
        occ_clean = occ.strip() if isinstance(occ, str) else ""
        if not occ_clean:
            results.append(
                {
                    "queried_occupation": occ,
                    "ERROR": "Empty occupation title; nothing to analyze.",
                }
            )
            continue

        if headers:
            live = _fetch_onet_exposure(occ, occ_clean, headers)
            if live:
                results.append(live)
                continue

        # Fallback/Offline logic
        matched = _match_exposure_db(occ_clean.lower(), exposure_db)
        if matched:
            matched_data = matched.copy()
            matched_data["queried_occupation"] = occ
            matched_data["source"] = CURATED_ESTIMATE_SOURCE
            results.append(matched_data)
        else:
            results.append(
                {
                    "queried_occupation": occ,
                    "soc": "Unknown",
                    "exposure_level": "Unknown/Fuzzy Match",
                    "impact_mode": "Unknown",
                    "complexity_score": "Requires manual review",
                    "key_exposed_tasks": ["N/A"],
                    "recommendation": f"Data not pre-mapped for '{occ}'. Standard exposure for this role requires custom task-level evaluation.",
                    "source": "None (occupation not pre-mapped; no data)",
                }
            )

    return json.dumps(results, indent=2)


def _fetch_onet_exposure(
    occ: str, occ_clean: str, headers: dict[str, str]
) -> dict | None:
    """Fetches O*NET tasks and classifies them; returns None on failure."""
    # Step A: Search for the SOC code
    search_url = "https://api-v2.onetcenter.org/online/search"
    try:
        search_resp = requests.get(
            search_url,
            params={"keyword": occ_clean, "limit": 1},
            headers=headers,
            timeout=HTTP_TIMEOUT_SECONDS,
        )
        if search_resp.status_code != 200:
            logger.info(
                "O*NET search returned HTTP %s; using curated estimates.",
                search_resp.status_code,
            )
            return None
        occupation_list = search_resp.json().get("occupation", [])
        if not occupation_list:
            return None
        code = occupation_list[0].get("code")
        official_title = occupation_list[0].get("title")

        # Step B: Fetch tasks
        tasks_url = f"https://api-v2.onetcenter.org/online/occupations/{code}/details/tasks"
        tasks_resp = requests.get(
            tasks_url, headers=headers, timeout=HTTP_TIMEOUT_SECONDS
        )
        if tasks_resp.status_code != 200:
            return None
        task_items = tasks_resp.json().get("task", [])
        task_titles = [t.get("title") for t in task_items if t.get("title")][
            :10
        ]
        if not task_titles:
            return None

        # Step C: Query Gemini to analyze tasks
        analysis = classify_onet_tasks_with_gemini(official_title, task_titles)
    except Exception as e:
        logger.warning(
            "O*NET live fetch/analysis failed: %s. Falling back to curated "
            "estimates.",
            safe_error(e),
        )
        return None

    failed = bool(analysis.get("classification_failed"))
    return {
        "soc": code,
        "exposure_level": analysis.get("exposure_level", "Unknown"),
        "impact_mode": analysis.get("impact_mode", "Unknown"),
        "complexity_score": analysis.get(
            "complexity_score", "Requires manual review"
        ),
        "key_exposed_tasks": analysis.get("key_exposed_tasks", task_titles[:3]),
        "recommendation": analysis.get(
            "recommendation", "Review the O*NET task list manually."
        ),
        "queried_occupation": occ,
        "source": CLASSIFICATION_FAILED_SOURCE
        if failed
        else GEMINI_ESTIMATE_SOURCE,
    }
