"""Initial program for Deep Research Whitepaper Generation Orchestrator.

Develop a multi-step orchestration pipeline and prompt chain (Planner -> Researcher -> Auditor -> Scribe) that generates a deeply researched, comprehensive, data-dense, McKinsey-style Markdown whitepaper based on a consultative economic research goal. It must ground its claims in live API data and external web search, correlate derived metrics across sources, and enforce correct URL citations at the end of the report. Avoid asking the user for complementary steps; retrieve everything required in a single flow.
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
# IMPORTANT: Keep the function name as 'solve' and signature identical.
# Evolve this block to transition from simple Q&A into deep research whitepaper synthesis.

def solve(eval_inputs: Mapping[str, Any]) -> str:
    """
    Generates a deeply researched whitepaper on the provided topic.
    """
    topic = eval_inputs.get("research_topic", "")
    
    if not topic:
        return "ERROR: No research topic provided."

    # Baseline Implementation: Invoke the standard Economic Research Agent App container once.
    # This serves as the naive "single-turn Q&A" baseline.
    try:
        from economic_research.agent import export_agent
        
        # Run the agent synchronously using its top-level query method
        final_response = export_agent.query(topic)
        return final_response
        
    except Exception as e:
        logger.error(f"Failed to execute baseline Economic Research Agent: {e}")
        return f"Error executing research agent: {e}"

# EVOLVE-BLOCK-END


def evaluate(eval_inputs: Mapping[str, Any]) -> dict[str, float]:
    """Score the solution using a composite multi-objective pipeline.
    
    Weights:
      - 40% Narrative Professionalism & Formatting
      - 30% Data Grounding Rigor
      - 20% Synthesis & Cross-Source Correlation
      - 10% Citation Compliance
    """
    try:
        # Step 1: Execute the orchestrator
        report = solve(eval_inputs)
        
        # Step 2: Validate basic structure
        if not report or not isinstance(report, str) or len(report) < 300:
            logger.warning(f"Report rejected due to insufficient length or invalid type: {type(report)}")
            return {
                "composite_quality_score": -10**12,
                "narrative_professionalism": 0.0,
                "data_grounding_rigor": 0.0,
                "synthesis_correlations": 0.0,
                "citation_compliance": 0.0
            }
            
        report_lower = report.lower()
        
        # Heuristics
        has_intro = int("# intro" in report_lower or "# executive summary" in report_lower or "executive summary" in report_lower)
        has_data = int("# data analysis" in report_lower or "# methodology" in report_lower or "methodology" in report_lower or "data analysis" in report_lower)
        has_table = int("|---" in report or "| ---" in report)
        has_citations = int("http://" in report or "https://" in report or ".gov" in report_lower or ".org" in report_lower)
        
        # Step 3: LLM Critic Grading (McKinsey Partner persona)
        # Load API keys from the agent's actual .env file
        env_path = "/Users/enriq/Documents/adk-samples/python/agents/economic-research-agent/.env"
        load_dotenv(env_path)
        
        if not os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_CLOUD_PROJECT"):
            logger.error("Neither GEMINI_API_KEY nor GOOGLE_CLOUD_PROJECT were found. Cannot authenticate with GenAI.")
            return {"composite_quality_score": -10**12}

        
        from google import genai
        from google.genai import types
        
        # Use google-genai to instantiate the client
        client = genai.Client()
        
        grading_prompt = f"""
        You are a Senior Managing Partner at a top-tier global strategy consulting firm (like McKinsey, BCG, or Bain).
        Audit the following economic research brief/whitepaper. Grade its quality on a continuous scale from 0.0 (Unacceptable/Terrible) to 10.0 (World-Class/Publishable).
        
        Provide grades for exactly four categories as a valid JSON object:
        1. "narrative": Narrative flow, structured headings, professional consulting tone, and readability.
        2. "grounding": Rigor and presence of real numeric data fetched from economic APIs (e.g. GDP, unemployment rates, utility rates, FMR rents, tax rates).
        3. "synthesis": Cross-source correlations and derivations (e.g. creating scorecards, correlating tax with electricity, or comparing complex derived relocation shifts across MSAs).
        4. "citations": Inclusion of verified URL endpoints or data sources at the end of the brief.
        
        Do not include markdown tags (like ```json), explanations, or text before/after the JSON.
        
        ### Target Topic:
        {eval_inputs.get("research_topic")}
        
        ### Whitepaper Content:
        {report}
        """
        
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=grading_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            grades = json.loads(response.text.strip())
        except Exception as e:
            logger.error(f"Grading LLM failed: {e}")
            # Fallback to pure heuristics if the grading LLM hits rate limits or errors
            grades = {
                "narrative": (has_intro + has_data + has_table) * 3.3,
                "grounding": 5.0 if has_table else 2.0,
                "synthesis": 3.0 if has_table else 1.0,
                "citations": 10.0 if has_citations else 0.0
            }
            
        s_narrative = float(grades.get("narrative", 0.0))
        s_grounding = float(grades.get("grounding", 0.0))
        s_synthesis = float(grades.get("synthesis", 0.0))
        s_citations = float(grades.get("citations", 0.0))
        
        # Balance heuristics with LLM grading
        s_narrative = (s_narrative + (has_intro + has_data + has_table) * 3.3) / 2.0
        s_citations = (s_citations + has_citations * 10.0) / 2.0
        
        # Cap scores between 0 and 10
        s_narrative = max(0.0, min(10.0, s_narrative))
        s_grounding = max(0.0, min(10.0, s_grounding))
        s_synthesis = max(0.0, min(10.0, s_synthesis))
        s_citations = max(0.0, min(10.0, s_citations))
        
        # Calculate Blended Composite Scalar Score
        # Weights: 40% Narrative, 30% Grounding, 20% Synthesis, 10% Citations
        composite = (0.40 * s_narrative) + (0.30 * s_grounding) + (0.20 * s_synthesis) + (0.10 * s_citations)
        
        if math.isnan(composite) or math.isinf(composite):
            logger.warning(f"Composite score is non-finite: {composite}")
            return {"composite_quality_score": -10**12}
            
        logger.info(f"🧬 Evolved Program Evaluation Result: Composite={composite:.2f} (N={s_narrative:.1f}, G={s_grounding:.1f}, S={s_synthesis:.1f}, C={s_citations:.1f})")
        
        return {
            "composite_quality_score": composite,
            "narrative_professionalism": s_narrative,
            "data_grounding_rigor": s_grounding,
            "synthesis_correlations": s_synthesis,
            "citation_compliance": s_citations
        }
        
    except Exception as e:
        logger.error(f"Top-level evaluation exception: {e}")
        return {"composite_quality_score": -10**12}

if __name__ == "__main__":
    # Local verification run
    test_inputs = {
        "research_topic": "Compare the Real GDP growth rate, industrial electricity rates, and workforce AI exposure risk for a new tech and manufacturing hub between Austin, TX and Columbus, OH."
    }
    print("🚀 Running local solve() and evaluate()...")
    res = evaluate(test_inputs)
    print(json.dumps(res, indent=2))
