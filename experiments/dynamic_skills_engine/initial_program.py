"""Initial program for Evolved Dynamic Skills Adapter Engine.

Develop a unified dynamic skill adapter engine and execution wrapper `execute_skill(skill_name: str, **kwargs) -> str` that enhances all 29 underlying Economic Research Agent tools. When a skill is invoked with an unknown, non-hardcoded entity (like a tier-2 city, non-standard MSA, county FIPS, or obscure commodity code), the engine must autonomously resolve the missing identifiers via live Serper search or API discovery, cache the mappings locally, and dynamically execute the fetch. It must gracefully fallback to live data scraping if an endpoint returns an error or empty payload.
"""

import json
import logging
import math
import os
import re
from typing import Any, Mapping
from dotenv import load_dotenv

# Load and Map ERA .env variables to Google Cloud / Vertex AI standards
env_path = "/Users/enriq/Documents/adk-samples/python/agents/economic-research-agent/.env"
load_dotenv(env_path)

if not os.getenv("GOOGLE_CLOUD_PROJECT"):
    os.environ["GOOGLE_CLOUD_PROJECT"] = os.getenv("PROJECT_ID", "project-maui")
if not os.getenv("GOOGLE_GENAI_USE_VERTEXAI"):
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "1"
if not os.getenv("GOOGLE_CLOUD_LOCATION"):
    os.environ["GOOGLE_CLOUD_LOCATION"] = os.getenv("LOCATION", "us-central1")
if not os.getenv("GCP_PROJECT"):
    os.environ["GCP_PROJECT"] = os.getenv("PROJECT_ID", "project-maui")

# Set up logging for insights
logger = logging.getLogger(__name__)


# EVOLVE-BLOCK-START
# IMPORTANT: Keep the function name as 'execute_skill' and signature identical.
# Evolve this block to introduce dynamic entity discovery (FIPS/MSA/HS-Codes) and caching.

def execute_skill(skill_name: str, **kwargs) -> str:
    """
    Executes an underlying economic research tool, dynamically resolving missing mappings.
    """
    skill_clean = skill_name.strip().lower()
    
    if skill_clean == "fred":
        try:
            from economic_research.tools.fred_skill import fetch_regional_macro_stats
            city = kwargs.get("city", kwargs.get("city_names", ["Austin"])[0])
            series_type = kwargs.get("metric", kwargs.get("series_type", "unemployment"))
            
            # Baseline simply passes the raw string to the hardcoded/search skill
            return fetch_regional_macro_stats(city_names=[city], series_type=series_type)
        except Exception as e:
            return f"ERROR [fred]: {e}"
            
    elif skill_clean == "hud":
        try:
            from economic_research.tools.hud_skill import fetch_hud_fmr_data
            city_or_fips = kwargs.get("city", kwargs.get("county_fips", "Austin"))
            
            # Baseline invokes directly
            return fetch_hud_fmr_data(county_fips=city_or_fips)
        except Exception as e:
            return f"ERROR [hud]: {e}"
            
    elif skill_clean == "trade":
        try:
            from economic_research.tools.trade_skill import fetch_regional_trade_data
            state = kwargs.get("state", kwargs.get("state_names", ["Texas"])[0])
            commodity = kwargs.get("commodity", "Electronic Products")
            
            # Baseline invokes directly
            return fetch_regional_trade_data(state_names=[state], commodity=commodity)
        except Exception as e:
            return f"ERROR [trade]: {e}"
            
    return f"ERROR: Skill '{skill_name}' is not supported by the dynamic adapter engine."

# EVOLVE-BLOCK-END


def solve(eval_inputs: Mapping[str, Any]) -> dict[str, str]:
    """Applies the evolved engine to execute all requested test cases."""
    results = {}
    test_cases = eval_inputs.get("test_cases", [])
    
    for tc in test_cases:
        skill = tc.get("skill", "")
        key_name = f"{skill}_{tc.get('city', tc.get('state', 'unknown'))}"
        
        try:
            output = execute_skill(skill, **tc)
            results[key_name] = output
        except Exception as e:
            results[key_name] = f"EXCEPTION: {e}"
            
    return results


def evaluate(eval_inputs: Mapping[str, Any]) -> dict[str, float]:
    """Scores the evolved DynamicSkillEngine based on execution coverage and resilience."""
    try:
        # Step 1: Run all test cases
        outputs = solve(eval_inputs)
        
        s_coverage = 0.0
        s_resilience = 0.0
        
        test_cases = eval_inputs.get("test_cases", [])
        total_tests = len(test_cases)
        
        if total_tests == 0:
            return {"coverage_and_resilience_score": -10**12}
            
        for tc in test_cases:
            skill = tc.get("skill", "")
            entity = tc.get("city", tc.get("state", "unknown"))
            key_name = f"{skill}_{entity}"
            
            result = outputs.get(key_name, "")
            
            # Check for valid, non-error data extraction AND true entity grounding
            if result and "ERROR" not in result and "EXCEPTION" not in result and len(result) > 50:
                result_lower = result.lower()
                entity_clean = entity.split(',')[0].strip().lower()
                
                # Broaden to check for county fallbacks (e.g. Ada for Boise, Franklin for Columbus)
                entity_synonyms = {
                    "boise": ["boise", "ada", "16001"],
                    "columbus": ["columbus", "franklin", "39049"],
                    "idaho": ["idaho", "id"]
                }
                syns = entity_synonyms.get(entity_clean, [entity_clean])
                
                has_grounding = any(s in result_lower for s in syns)
                
                if has_grounding:
                    s_coverage += 1.0
                    
                    # Check for numerical data presence (indicating actual API hit, not fallback error strings)
                    has_num = bool(re.search(r'\d+', result))
                    has_dollar_or_pct = ('$' in result or '%' in result or '202' in result)
                    
                    if has_num and has_dollar_or_pct:
                        s_resilience += 1.0
                    
        # Calculate coverage ratio
        coverage_ratio = s_coverage / total_tests
        resilience_ratio = s_resilience / total_tests
        
        # Blended Score: 60% Coverage (does it return data?), 40% Resilience (is it real API numeric data?)
        composite = (0.60 * coverage_ratio * 10.0) + (0.40 * resilience_ratio * 10.0)
        
        logger.info(f"🧬 Evolved SkillEngine Evaluation Result: Composite={composite:.2f} (Coverage={coverage_ratio*10:.1f}, Resilience={resilience_ratio*10:.1f})")
        
        if math.isnan(composite) or math.isinf(composite):
            return {"coverage_and_resilience_score": -10**12}
            
        return {
            "coverage_and_resilience_score": composite,
            "coverage_depth": coverage_ratio * 10.0,
            "api_resilience": resilience_ratio * 10.0
        }
        
    except Exception as e:
        logger.error(f"Top-level evaluation exception in SkillEngine: {e}")
        return {"coverage_and_resilience_score": -10**12}


if __name__ == "__main__":
    test_inputs = {
        "test_cases": [
            {
                "skill": "fred",
                "city": "Columbus, OH",
                "metric": "unemployment"
            },
            {
                "skill": "hud",
                "city": "Boise, ID",
                "metric": "fmr_2br"
            },
            {
                "skill": "trade",
                "state": "Idaho",
                "commodity": "Semiconductors"
            }
        ]
    }
    print("🚀 Running local execute_skill() and evaluate()...")
    res = evaluate(test_inputs)
    print(json.dumps(res, indent=2))
