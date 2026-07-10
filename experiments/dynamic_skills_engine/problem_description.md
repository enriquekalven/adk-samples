# Evolved Dynamic Skills Adapter Engine

## Problem Description
You are developing a unified dynamic skill adapter engine and execution wrapper `execute_skill(skill_name: str, **kwargs) -> str` that enhances all 29 underlying **Economic Research Agent** tools. 

Currently, the tools in `economic_research/tools/` rely on rigid, hardcoded heuristics (e.g. fixed lists of top-20 cities, top-8 MSAs, or static offline Data Banks). Your goal is to optimize the `# EVOLVE-BLOCK` inside `execute_skill()` to autonomously resolve missing mappings for ANY tier-2/tier-3 city, complex county, non-standard MSA, or obscure commodity code. 

The evolved engine must:
* Intercept requests, check for missing mappings in the native tool's heuristics, and invoke **Serper.dev** or API discovery dynamically to resolve the accurate FIPS, MSA, or HS Commodity code.
* Store newly discovered mappings in a runtime Local Entity Cache so subsequent calls bypass the discovery latency.
* Execute the target fetch successfully with the resolved identifiers.
* Provide resilient scrapers/fallbacks to live web search if the native API endpoint degrades or returns empty payloads.

## Search Space
Your modifications are restricted to the code between `# EVOLVE-BLOCK-START` and `# EVOLVE-BLOCK-END`. You have full freedom to:
* Design regex, parsing, and Serper discovery algorithms to find and validate FIPS/MSA/HS codes on the fly.
* Implement a runtime cache using dictionaries or local state.
* Inject graceful API error-handling and connection timeouts.

## Constraints
* **Keep the function name as 'execute_skill' and signature identical**.
* Must return identical data output formats (JSON strings or Markdown) to the underlying native skills for downstream Scribe parser compatibility.
* **Return valid, finite scores** in the evaluator.
