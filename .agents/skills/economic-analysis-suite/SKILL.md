---
name: economic-analysis-suite
description: Standalone Economic Analysis Suite containing MLS active listings, Census trade flows, O*NET task AI exposure, and FRED labor disruption modeling tools.
---

# Economic Analysis Suite

This skill provides modular economic analysis tools for real estate and workforce consulting. It can be loaded by other agents, or executed as a standalone CLI tool without agent deployment.

## Included Tools

1. **MLS Active Listings & Yield Calculator**: Fetches property listings via RentCast, county FIPS mappings, and computes Cap Rates using local HUD rents.
2. **Census Trade Flows**: Fetches real-time trade exports by state and HS commodity code from the U.S. Census Bureau.
3. **O*NET Occupational AI Exposure**: Resolves job titles to O*NET SOC codes, fetches DOL task lists, and evaluates task-level exposure via Gemini.
4. **FRED Labor Disruption**: Calculates regional AI Vulnerability Indices dynamically using St. Louis Fed sector employment data.

## Standalone Usage

Navigate to the `scripts/` directory and execute analysis queries directly from the CLI:

```bash
# Fetch active properties and Cap Rates in Columbus, OH
python3 run_analysis.py properties --city Columbus --type multifamily

# Analyze AI labor exposure for specific occupations
python3 run_analysis.py exposure --jobs "Software Developers" "Customer Service Representatives"

# Fetch trade flows for pharmaceuticals in North Carolina
python3 run_analysis.py trade --states "North Carolina" --commodity "Pharmaceuticals"

# Compare labor market disruption in Austin and Raleigh
python3 run_analysis.py disruption --cities Austin Raleigh
```
