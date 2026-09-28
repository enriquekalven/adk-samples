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

# economic_research package
"""Atomic Agent: Economic Research Agent (ERA)."""

import logging
import os
from pathlib import Path

import google.auth
from dotenv import dotenv_values, load_dotenv

# Load variables from .env if present. In production the environment is
# already populated by the platform (Cloud Run, GKE, etc.), so a missing
# .env is expected and not an error.
load_dotenv()
for _k, _v in dotenv_values(
    Path(__file__).resolve().parent.parent / ".env.example"
).items():
    if _v is not None and not _v.startswith("<TODO:") and _k not in os.environ:
        os.environ[_k] = _v
for _k, _v in list(os.environ.items()):
    if _v.startswith("<TODO:"):
        del os.environ[_k]

try:
    _, project_id = google.auth.default()
    if project_id:
        if "GOOGLE_CLOUD_PROJECT" not in os.environ:
            os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
except Exception as exc:
    logging.getLogger(__name__).debug(
        "Default credentials unavailable: %s", exc
    )


from .agent import agent  # noqa: E402 -- must come after load_dotenv()
