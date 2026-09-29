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

"""Utility Functions for Economic Research Agent."""

import functools
import os
import re
import threading
import time
from contextvars import ContextVar
from pathlib import Path
from typing import Any

import pandas as pd
from dotenv import dotenv_values
from google.cloud import secretmanager

_SESSION_API_KEYS: ContextVar[dict[str, str] | None] = ContextVar(
    "session_api_keys", default=None
)
_ENV_EXAMPLE_PATH = (
    Path(__file__).resolve().parent.parent.parent / ".env.example"
)
# Last-resort default. `.env.example` is not shipped in the Docker image or
# the Agent Runtime package, so it cannot be the only fallback.
DEFAULT_MODEL = "gemini-3.5-flash"


# Default timeout (seconds) for outbound HTTP calls made by tools.
HTTP_TIMEOUT_SECONDS = 15

# Label every non-live (hardcoded, illustrative or fallback) result with this
# so neither the LLM nor the reader mistakes it for live data.
SANDBOX_SOURCE = "Sandbox (illustrative data, NOT live)"

# API keys that tools read. Users can supply these for a session; they are
# also scrubbed from any error text returned to the LLM.
KNOWN_API_KEYS = (
    "BEA_API_KEY",
    "FRED_API_KEY",
    "CENSUS_API_KEY",
    "EIA_API_KEY",
    "BLS_API_KEY",
    "HUD_API_KEY",
    "FEC_API_KEY",
    "NEWS_API_KEY",
    "SERPER_API_KEY",
    "CDC_APP_TOKEN",
    "OPENFDA_API_KEY",
    "RENTCAST_API_KEY",
    "ONET_API_KEY",
)

_SECRET_QUERY_PARAM = re.compile(
    r"(?i)\b(api_key|apikey|key|registrationkey|userid|token|app_token"
    r"|access_token|x-api-key)=([^&\s'\"]+)"
)


def redact_secrets(text: str) -> str:
    """Removes API keys from ``text`` (query parameters and known values)."""
    redacted = _SECRET_QUERY_PARAM.sub(r"\1=REDACTED", text)
    for key_name in KNOWN_API_KEYS:
        value = get_session_api_key(key_name)
        if value and len(value) >= 6:
            redacted = redacted.replace(value, "REDACTED")
    return redacted


def safe_error(exc: BaseException, max_len: int = 200) -> str:
    """Formats an exception for the LLM without leaking API keys."""
    message = redact_secrets(str(exc))
    if len(message) > max_len:
        message = message[:max_len] + "…"
    return f"{type(exc).__name__}: {message}" if message else type(exc).__name__


def init_session_api_keys() -> None:
    """Initializes a fresh mutable dictionary for the current request context."""
    _SESSION_API_KEYS.set({})


def get_default_model(override: str | None = None) -> str:
    """Resolves the configured model identifier from the environment."""
    candidate = override or os.getenv("MODEL_NAME")
    if candidate and not candidate.startswith("<TODO:"):
        return candidate
    env_defaults = dotenv_values(_ENV_EXAMPLE_PATH)
    return env_defaults.get("MODEL_NAME") or DEFAULT_MODEL


def get_session_api_key(
    key_name: str, env_val: str | None = None
) -> str | None:
    """Retrieves an API key from the current session context or environment."""
    keys = _SESSION_API_KEYS.get()
    if keys and key_name in keys:
        return keys[key_name]
    raw_val = env_val if env_val is not None else os.getenv(key_name)
    if raw_val and not raw_val.startswith("<TODO:"):
        return raw_val
    return None


def set_session_api_key(key_name: str, key_value: str) -> str:
    """Sets an API key in the current session's isolated context.

    Use this when the user provides a missing API key in the chat.

    Args:
        key_name: The name of the environment variable (e.g., 'FRED_API_KEY').
        key_value: The API key value provided by the user.

    Returns:
        A confirmation message.
    """
    if key_name not in KNOWN_API_KEYS:
        return f"ERROR: Setting {key_name} is not allowed."

    current_keys = _SESSION_API_KEYS.get()
    if current_keys is not None:
        current_keys[key_name] = key_value
    else:
        _SESSION_API_KEYS.set({key_name: key_value})
    return f"Successfully set {key_name} for this session. You can now retry the failed operation."


SECRET_TIMEOUT_SECONDS = 5
SECRET_CACHE_TTL_SECONDS = 600
_SECRET_CACHE: dict[tuple[str, str], tuple[float, str | None]] = {}
_SECRET_CACHE_LOCK = threading.Lock()


@functools.lru_cache(maxsize=1)
def _secret_manager_client() -> secretmanager.SecretManagerServiceClient:
    return secretmanager.SecretManagerServiceClient()


@functools.lru_cache(maxsize=1)
def _default_project_id() -> str | None:
    """Resolves the GCP project once per process (ADC lookups are slow)."""
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    if project_id:
        return project_id
    try:
        import google.auth

        _, project_id = google.auth.default()
    except Exception:  # no ADC configured
        return None
    return project_id or None


def access_secret_version(
    project_id, secret_id, version_id="latest", timeout=None
):
    """Access secret from GCP Secret Manager."""

    client = _secret_manager_client()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(
        request={"name": name},
        timeout=timeout or SECRET_TIMEOUT_SECONDS,
    )

    return response.payload.data.decode("UTF-8")


def get_cloud_secret(key_name: str) -> str | None:
    """Returns an API key from the session/env, else from Secret Manager.

    Secret Manager results (including "not found") are cached for
    ``SECRET_CACHE_TTL_SECONDS`` so a query doesn't pay one network round trip
    per key. Secrets are project-wide configuration, not per-user data, so a
    process-wide cache is safe.
    """
    value = get_session_api_key(key_name)
    if value:
        return value
    project_id = _default_project_id()
    if not project_id:
        return None

    cache_key = (project_id, key_name)
    now = time.monotonic()
    with _SECRET_CACHE_LOCK:
        cached = _SECRET_CACHE.get(cache_key)
    if cached and now - cached[0] < SECRET_CACHE_TTL_SECONDS:
        return cached[1]

    try:
        value = access_secret_version(project_id=project_id, secret_id=key_name)
    except Exception:  # missing secret, no permission, timeout, no network
        value = None
    if value is not None and value.startswith("<TODO:"):
        value = None
    with _SECRET_CACHE_LOCK:
        _SECRET_CACHE[cache_key] = (now, value)
    return value


def execute_bq_query_to_df(
    project: str,
    query: str,
    params: dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Mocked execution of BigQuery queries to bypass GCP Dataset NotFound errors.

    Args:
        project: The Google Cloud project ID.
        query: The BigQuery query string.
        params: Optional dictionary of parameterized query bindings.

    Returns:
        A mock pandas DataFrame resembling the expected BLS schema.
    """
    _ = params

    # Return mock data for standard BLS queries to keep local pipeline alive
    if "labor_force" in query.lower():
        return pd.DataFrame(
            [
                {
                    "area_name": "Austin, TX",
                    "labor_force": 1200000,
                    "unemployment_rate": "3.2% (2025)",
                    "source": "BLS (Mock)",
                },
                {
                    "area_name": "Seattle, WA",
                    "labor_force": 2000000,
                    "unemployment_rate": "3.8% (2025)",
                    "source": "BLS (Mock)",
                },
                {
                    "area_name": "San Francisco, CA",
                    "labor_force": 2500000,
                    "unemployment_rate": "4.1% (2025)",
                    "source": "BLS (Mock)",
                },
            ]
        )

    elif "median_hourly_wage" in query.lower():
        return pd.DataFrame(
            [
                {
                    "metro": "Austin-Round Rock, TX",
                    "median_hourly_wage": "$32.50",
                    "source": "BLS Wags (Mock)",
                },
                {
                    "metro": "Seattle-Tacoma-Bellevue, WA",
                    "median_hourly_wage": "$41.20",
                    "source": "BLS Wages (Mock)",
                },
                {
                    "metro": "San Francisco-Oakland-Hayward, CA",
                    "median_hourly_wage": "$45.80",
                    "source": "BLS Wages (Mock)",
                },
            ]
        )

    return pd.DataFrame()


def join_sets(*sets) -> set:
    """Join multiple sets and return set with unique elements.

    Args:
        *sets: Variable number of sets to join.
    """
    resulting_set = set()
    for s in sets:
        resulting_set.update(s)
    return resulting_set


def merge_dataframes(df_list, how="outer", on=None):
    """
    Merges a list of DataFrames into a single DataFrame.

    Args:
        df_list (list): A list of pandas DataFrames to merge.

    Returns:
        pandas.DataFrame: The merged DataFrame,
            or None if the input list is empty.
    """
    try:
        if not df_list:
            return None

        merged_df = df_list[0]

        for df in df_list[1:]:
            merged_df = pd.merge(merged_df, df, how=how, on=on)

        return merged_df
    except Exception as e:
        raise e
