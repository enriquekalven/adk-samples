#!/usr/bin/env python3
"""AlphaEvolve 20-Iteration Hill-Climbing Suite.
Executes 20 strategic corporate WOW queries, tracks Actor-Critic corrections, 
and aggregates production-grade Observability metrics.
"""

import os
import sys
import time
import json
import logging
import traceback
from tenacity import retry, stop_after_attempt, wait_exponential

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


from economic_research.agent import ERAAgent
from economic_research.orchestrators.universal_whitepaper_orchestrator import solve as universal_solve

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ARTIFACT_DIR = "/Users/enriq/.gemini/jetski/brain/8e93cb21-a500-4e6b-8e51-3f47b790ae28"
OBS_DIR = "/Users/enriq/.gemini/jetski/scratch/observability"
SCORECARD_PATH = os.path.join(ARTIFACT_DIR, "alphaevolve_20x_scorecard.md")

QUERIES = [
    ("Scenario 01", "Select optimal Tech Hub comparing Nashville, TN, Austin, TX, and Provo, UT"),
    ("Scenario 02", "Underwrite multifamily cap rates in Tampa, FL vs Orlando, FL against HUD FMR rents"),
    ("Scenario 03", "Forecast AI displacement for Logistics Managers in Detroit, MI vs Chicago, IL"),
    ("Scenario 04", "Analyze Georgia as an EV battery manufacturing hub integrating USITC trade flows and Good Jobs First abatements"),
    ("Scenario 05", "Compare Seattle, WA and Boston, MA for a new Life Sciences R&D Hub Site Selection"),
    ("Scenario 06", "Find multifamily investment properties in Charlotte, NC vs Raleigh, NC and estimate Cap Rates"),
    ("Scenario 07", "Forecast AI task exposure for Financial Analysts in NYC vs Charlotte, NC"),
    ("Scenario 08", "Analyze Texas vs New Mexico for oil and energy supply chain regulatory policy and Federal Register notices"),
    ("Scenario 09", "Compare Boise, ID and Reno, NV for a regional fulfillment and Logistics Hub using DOT BTS data"),
    ("Scenario 10", "Underwrite multifamily cap rates in Phoenix, AZ vs Tucson, AZ using RentCast and HUD data"),
    ("Scenario 11", "Forecast AI automation risk for Healthcare Admins in Houston, TX vs Dallas, TX"),
    ("Scenario 12", "Analyze New York vs New Jersey for Fintech tax incentives, credits, and USITC trade flows"),
    ("Scenario 13", "Compare Indianapolis, IN and Columbus, OH for agricultural biotech site selection using EIA and BLS data"),
    ("Scenario 14", "Underwrite multifamily properties in Las Vegas, NV using HUD FMRs and RentCast"),
    ("Scenario 15", "Forecast AI displacement for Software QA Engineers in San Francisco, CA vs Austin, TX"),
    ("Scenario 16", "Analyze Alabama vs Tennessee for aerospace supply chain abatements and manufacturing incentives"),
    ("Scenario 17", "Compare Salt Lake City, UT and Denver, CO for data center utility power capacity and EIA industrial rates"),
    ("Scenario 18", "Underwrite Real Estate Cap Rates in Austin, TX for student housing near UT Austin"),
    ("Scenario 19", "Forecast AI disruption for Paralegals and legal operations in Washington, DC vs NYC"),
    ("Scenario 20", "Analyze Michigan vs Ohio for automotive CHIPS Act supply chain resilience and USITC trade dependencies")
]

def load_observability_primitive(obs_path: str) -> dict:
    try:
        with open(obs_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def run_hillclimb():
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    os.makedirs(OBS_DIR, exist_ok=True)
    
    scorecard = {
        "total_iterations": len(QUERIES),
        "successful_iterations": 0,
        "failed_iterations": 0,
        "total_self_corrections": 0,
        "results": []
    }
    
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   🧬 EXECUTING 20-ITERATION ALPHAEVOLVE SUITE 🧬         ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    for idx, (label, query) in enumerate(QUERIES, start=1):
        print(f"\n🚀 [{idx}/20] Iterating: {label}...")
        print(f"   Query: '{query}'")
        
        start_time = time.time()
        obs_before = set(os.listdir(OBS_DIR))
        
        try:
            @retry(
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=1, min=10, max=60),
                reraise=True
            )
            def execute_with_retry(inputs):
                return universal_solve(inputs)

            # Execute Phase 1 & 2 via Orchestrator
            eval_inputs = {"research_topic": query}
            result_md = execute_with_retry(eval_inputs)
            
            elapsed = time.time() - start_time
            obs_after = set(os.listdir(OBS_DIR)) - obs_before
            
            # Extract Observability Metrics
            actor_critic_corrections = 0
            task_success = True
            
            for new_obs_file in obs_after:
                full_obs_path = os.path.join(OBS_DIR, new_obs_file)
                obs_data = load_observability_primitive(full_obs_path)
                if obs_data.get("interaction_type") == "feedback_loop":
                    actor_critic_corrections += 1
                if obs_data.get("task_success") is False:
                    task_success = False
            
            if task_success and "ERROR" not in result_md:
                scorecard["successful_iterations"] += 1
            else:
                scorecard["failed_iterations"] += 1
                task_success = False
                
            scorecard["total_self_corrections"] += actor_critic_corrections
            
            res_entry = {
                "scenario": label,
                "query": query,
                "status": "SUCCESS" if task_success else "FAILED",
                "execution_time_seconds": round(elapsed, 2),
                "self_corrections": actor_critic_corrections
            }
            scorecard["results"].append(res_entry)
            print(f"   ✅ Completed in {res_entry['execution_time_seconds']}s (Corrections: {res_entry['self_corrections']})")
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"   ❌ Failed: {e}")
            scorecard["failed_iterations"] += 1
            scorecard["results"].append({
                "scenario": label,
                "query": query,
                "status": "FAILED",
                "execution_time_seconds": round(elapsed, 2),
                "self_corrections": 0,
                "error": str(e)
            })
            
        # 20-second sleep to respect API rate limits beautifully
        time.sleep(20)
        

    # Write Final Markdown Scorecard Artifact
    with open(SCORECARD_PATH, "w", encoding="utf-8") as f:
        f.write("# 🧬 AlphaEvolve 20-Iteration Hill-Climbing Scorecard\n\n")
        f.write(f"**Execution Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Total Scenarios**: {scorecard['total_iterations']}\n")
        f.write(f"**Successful**: {scorecard['successful_iterations']} ✅\n")
        f.write(f"**Failed**: {scorecard['failed_iterations']} ❌\n")
        f.write(f"**Total Actor-Critic Self-Corrections**: {scorecard['total_self_corrections']} ⚠️\n\n")
        
        f.write("## 📊 Scenario Metrics\n\n")
        f.write("| Scenario | Status | Time (s) | Critic Corrections | Target Query |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- |\n")
        for res in scorecard["results"]:
            status_emoji = "✅ SUCCESS" if res["status"] == "SUCCESS" else "❌ FAILED"
            f.write(f"| {res['scenario']} | {status_emoji} | {res['execution_time_seconds']} | {res['self_corrections']} | {res['query']} |\n")
            
    print(f"\n🥂 All 20 AlphaEvolve Hill-Climbing Iterations Completed! Scorecard saved to: {SCORECARD_PATH}")

if __name__ == "__main__":
    run_hillclimb()
