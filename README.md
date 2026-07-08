# Economic Analysis Suite - Standalone Customization Skill

This directory contains the **Economic Analysis Suite** customization skill, which packages real-time economic data sourcing tools (RentCast MLS, Census Trade, O*NET Job Tasks, FRED Labor Shifts) into a single standalone module.

## Directory Structure

```text
.agents/skills/economic-analysis-suite/
  ├── SKILL.md            # Custom skill definitions and parameters
  ├── README.md           # This developer guide
  └── scripts/
        ├── hud_skill.py                    # Live HUD FMR and USPS crosswalk client
        ├── mls_property_analysis_skill.py  # MLS active listings Cap Rate calculator
        ├── workforce_exposure_skill.py     # O*NET occupation SOC and task analyzer
        ├── trade_skill.py                  # Census statehs trade exports mapper
        ├── labor_shift_skill.py            # FRED regional employment shares modeler
        └── run_analysis.py                 # Standalone CLI runner script
```

## Prerequisite Setup

### 1. Install Dependencies
Run the following command to install the required Python libraries for the standalone suite:
```bash
pip install requests fredapi google-genai python-dotenv pydantic
```

### 2. Configure Environment Variables
Create a `.env` file in the root of the suite or define these environment variables in your shell:
```text
# Sourcing Credentials
CENSUS_API_KEY=your_census_key_here
FRED_API_KEY=your_fred_key_here
HUD_API_KEY=your_hud_jwt_bearer_token_here
RENTCAST_API_KEY=your_rentcast_api_key_here
ONET_API_KEY=your_onet_api_key_here

# Vertex AI Google GenAI Configuration (for Workforce AI exposure model)
GCP_PROJECT=your_gcp_project_id
GCP_LOCATION=us-central1
```

## Standalone Usage

Execute queries directly via the CLI runner:

```bash
cd scripts/

# 1. Properties Sourcing (RentCast API + HUD)
python3 run_analysis.py properties --city Columbus --type multifamily

# 2. Labor Market Disruption (FRED API)
python3 run_analysis.py disruption --cities Austin Columbus

# 3. Workforce AI Exposure (O*NET API + Gemini)
python3 run_analysis.py exposure --jobs "Software Developers"

# 4. Regional Trade Flows (Census statehs API)
python3 run_analysis.py trade --states "North Carolina" --commodity "Pharmaceuticals"

# 5. Housing Affordability (HUD User API FMR vs. AMI Limits)
python3 run_analysis.py affordability --city-or-fips Austin
```
