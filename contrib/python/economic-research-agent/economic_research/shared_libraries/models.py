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

"""Pydantic models for Economic Research Agent (ERA)."""

from pydantic import BaseModel


class MetroMatrix(BaseModel):
    """Metro Matrix workflow object."""

    city: str | None = None
    state: str | None = None
    county: str | None = None


class HQRelocation(BaseModel):
    """Head Quarter Relocation workflow object."""

    city: str | None = None
    state: str | None = None
    county: str | None = None
    industry: str | None = None


class CompanyRelocation(BaseModel):
    """Company Relocation workflow object."""

    city: str | None = None
    state: str | None = None
    county: str | None = None
    industry: str | None = None


class MetroMatrixResult(BaseModel):
    """Metro Matrix analysis result object."""

    city_analysis: list[MetroMatrix] = []
    error: str | None = None


class HQRelocationResult(BaseModel):
    """Head Quarter Relocation analysis result object."""

    city_analysis: list[HQRelocation] = []
    error: str | None = None


class CompanyRelocationResult(BaseModel):
    """Company Relocation analysis result object."""

    city_analysis: list[CompanyRelocation] = []
    error: str | None = None
