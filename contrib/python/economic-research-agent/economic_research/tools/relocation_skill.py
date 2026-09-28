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

"""ADK Skill: HR Employee Relocation Cost-of-Living Estimator."""

import json

from economic_research.tools.hud_skill import fetch_hud_fmr_data

# Simple top-bracket state individual income tax rates for key tech/finance hub states
INDIVIDUAL_TAX_RATES = {
    "CA": 13.3,
    "NY": 10.9,
    "NJ": 10.75,
    "MA": 9.0,
    "OR": 9.9,
    "NC": 4.5,
    "OH": 3.75,
    "GA": 5.49,
    "CO": 4.4,
    "TX": 0.0,
    "WA": 0.0,
    "FL": 0.0,
    "TN": 0.0,
    "NV": 0.0,
}


def estimate_employee_relocation(
    state_from: str,
    state_to: str,
    county_fips_from: str,
    county_fips_to: str,
    base_salary: float,
) -> str:
    """
    Estimates the net disposable income differential for an employee relocating between two regions.

    Args:
        state_from: 2-letter state code originating from (e.g., "CA").
        state_to: 2-letter state code moving to (e.g., "NC").
        county_fips_from: 5-digit county FIPS originating from (e.g., "06075" for San Francisco).
        county_fips_to: 5-digit county FIPS moving to (e.g., "37183" for Wake County/Raleigh).
        base_salary: Employee annual base salary in USD.

    Returns:
        JSON string detailing tax differences, rental savings, and net annual adjustment.
    """
    try:
        st_from = state_from.strip().upper()
        st_to = state_to.strip().upper()

        # 1. Tax Differentials
        tax_from = INDIVIDUAL_TAX_RATES.get(st_from, 5.0)
        tax_to = INDIVIDUAL_TAX_RATES.get(st_to, 5.0)

        estimated_tax_from = base_salary * (tax_from / 100.0)
        estimated_tax_to = base_salary * (tax_to / 100.0)
        tax_savings = estimated_tax_from - estimated_tax_to

        # 2. Housing Cost Differences (HUD 2BR FMR)
        rent_from = 1200.0  # Fallbacks
        rent_to = 1200.0

        try:
            fmr_from_res = json.loads(fetch_hud_fmr_data(county_fips_from))
            if "Rent_2BR" in fmr_from_res:
                rent_from = float(
                    fmr_from_res["Rent_2BR"]
                    .replace("$", "")
                    .replace(",", "")
                    .strip()
                )
        except Exception:
            rent_from = 1200.0

        try:
            fmr_to_res = json.loads(fetch_hud_fmr_data(county_fips_to))
            if "Rent_2BR" in fmr_to_res:
                rent_to = float(
                    fmr_to_res["Rent_2BR"]
                    .replace("$", "")
                    .replace(",", "")
                    .strip()
                )
        except Exception:
            rent_to = 1200.0

        annual_rent_from = rent_from * 12.0
        annual_rent_to = rent_to * 12.0
        housing_savings = annual_rent_from - annual_rent_to

        # 3. Combined net changes
        net_annual_differential = tax_savings + housing_savings

        return json.dumps(
            {
                "Relocation_Comparison": {
                    "Origin": f"{st_from} (FIPS: {county_fips_from})",
                    "Destination": f"{st_to} (FIPS: {county_fips_to})",
                    "Base_Salary": f"${base_salary:,.2f}",
                },
                "Annual_Cost_Analysis": {
                    "Estimated_State_Income_Tax": {
                        "Origin": f"${estimated_tax_from:,.2f} ({tax_from:.2f}%)",
                        "Destination": f"${estimated_tax_to:,.2f} ({tax_to:.2f}%)",
                        "Net_Tax_Savings": f"${tax_savings:,.2f}",
                    },
                    "Annualized_Housing_Cost_2BR_FMR": {
                        "Origin": f"${annual_rent_from:,.2f} (${rent_from:,.2f}/mo)",
                        "Destination": f"${annual_rent_to:,.2f} (${rent_to:,.2f}/mo)",
                        "Net_Housing_Savings": f"${housing_savings:,.2f}",
                    },
                },
                "Summary_Impact": {
                    "Net_Annual_Disposable_Income_Change": f"${net_annual_differential:,.2f}",
                    "Verdict": "Favorable"
                    if net_annual_differential > 0
                    else "Unfavorable",
                    "Explanation": (
                        f"Relocating to the destination provides an estimated net annual gain of "
                        f"${net_annual_differential:,.2f} in disposable income (after state tax and 2BR rent costs) "
                        "compared to staying in the origin."
                        if net_annual_differential > 0
                        else f"Relocating results in a net disposable income reduction of "
                        f"${abs(net_annual_differential):,.2f} due to tax/rent differentials."
                    ),
                },
                "Source": "Talent Relocation Decision Tool",
            },
            indent=2,
        )

    except Exception as e:
        return json.dumps(
            {"ERROR": f"Relocation estimation failed: {e!s}"}, indent=2
        )
