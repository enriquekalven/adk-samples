# Deep Research Whitepaper Generation Orchestrator

## Problem Description
You are developing a high-fidelity Deep Research orchestration pipeline and prompt-chain for the **Economic Research Agent**. 

Currently, the agent behaves as a single-turn Q&A bot (retrieving data for individual topics like "What is the unemployment rate in Austin?"). Your goal is to optimize the `# EVOLVE-BLOCK` inside `solve()` to generate a consultative, deeply-researched, McKinsey-style whitepaper for a given complex metropolitan or economic topic (e.g. comparing locations for corporate relocation or facility site selection). 

The generated whitepaper must:
* Be structured with formal Markdown headings (Executive Summary, Methodology, Data Analysis, Cross-Source Correlations, Recommendations).
* Ground all claims with real API and Serper web search data using the 29 available `economic_research` API tools.
* Calculate and highlight cross-source Derived Metrics (e.g. blending Tax Foundation rates + EIA energy costs + BLS wage statistics into a weighted Scorecard).
* Conclude with a dedicated "Sources & Citations" section containing valid URL links to the APIs used.

## Search Space
Your modifications are restricted to the code between `# EVOLVE-BLOCK-START` and `# EVOLVE-BLOCK-END`. You have full freedom to:
* Define and invoke multiple sub-agents (Planner, Researcher, Auditor, Scribe, Fact-Checker) using the ADK 2.0 framework installed in the environment.
* Design and refine the system instructions and user prompts passed to each LLM in your DAG pipeline.
* Implement parallel or sequential data harvesting using the available API tools and Serper search.
* Structure and iterate the synthesis logic that formats the final whitepaper.

## Constraints
* **Keep the function name as 'solve' and signature identical** (`solve(eval_inputs: Mapping[str, Any]) -> str`).
* Must return a valid Markdown string of sufficient depth (at least 300+ characters).
* Must not invoke prompt options requiring user onboarding/HITL in the final whitepaper generation turn (it should execute fully autonomously).
* **Return valid, finite scores** in the evaluator.
* Citations must be placed at the bottom of the whitepaper under a clean header.
