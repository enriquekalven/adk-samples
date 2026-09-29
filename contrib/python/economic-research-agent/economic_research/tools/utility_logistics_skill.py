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

"""ADK Skill: Infrastructure & Logistics (EIA & FCC Broadband Map)."""

import json

from pydantic import BaseModel, Field

from economic_research.shared_libraries.helper import SANDBOX_SOURCE


class UtilityRequest(BaseModel):
    state_names: list[str] = Field(
        ...,
        description="List of full state names to fetch utility/logistics data for.",
    )


def get_industrial_infrastructure_stats(state_names: list[str]) -> str:
    """
    Fetches commercial/industrial utility rates (EIA) and broadband infrastructure.
    For industrial/data-center moves, electricity rates and fiber-optic density are #1 cost drivers.
    """
    results = []

    for state in state_names:
        import us

        from economic_research.tools.eia_skill import (
            fetch_state_electricity_rates,
        )

        state_obj = us.states.lookup(state)
        state_code = state_obj.abbr if state_obj else state.upper().strip()

        raw_eia = (
            fetch_state_electricity_rates([state_code], sector="industrial")
            if len(state_code) == 2
            else "{}"
        )
        try:
            parsed_eia = json.loads(raw_eia)
            if (
                isinstance(parsed_eia, list)
                and len(parsed_eia) > 0
                and "Avg Price (cents/kWh)" in parsed_eia[0]
            ):
                # Raises ValueError on "N/A" (null EIA price) -> fallback.
                cents_kwh = float(parsed_eia[0]["Avg Price (cents/kWh)"])
                usd_kwh = f"${cents_kwh / 100:.3f}"
                period = parsed_eia[0].get("Period", "2024")
                results.append(
                    {
                        "State": state,
                        "Industrial Elec (kWh)": usd_kwh,
                        "Source": f"EIA Unified API Live ({period})",
                        # Not fetched from any API; static placeholders.
                        "Renewable Share (%)": "Moderate",
                        "Fiber Optic Density": "Tier 1",
                        "Infrastructure Source": SANDBOX_SOURCE,
                    }
                )
                continue
        except (TypeError, ValueError):
            parsed_eia = None

        # Live EIA data unavailable: static benchmark, clearly labelled.
        results.append(
            {
                "State": state,
                "Industrial Elec (kWh)": "$0.075",
                "Renewable Share (%)": "Moderate",
                "Fiber Optic Density": "Tier 1",
                "Source": f"{SANDBOX_SOURCE}: national industrial benchmark "
                "(live EIA data unavailable)",
            }
        )

    return json.dumps(results, indent=2)
