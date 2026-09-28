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

"""Pytest configuration for the Economic Research Agent recipe."""

import os
from pathlib import Path

from dotenv import dotenv_values

for _key, _val in dotenv_values(
    Path(__file__).resolve().parent.parent / ".env.example"
).items():
    if _val is not None and not _val.startswith("<TODO:"):
        os.environ.setdefault(_key, _val)
