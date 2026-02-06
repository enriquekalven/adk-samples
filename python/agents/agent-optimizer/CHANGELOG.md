# Changelog - Agent Optimizer

All notable changes to the Agent Optimizer will be documented in this file.

## [Unreleased] - 2026-01-27

### Added
- **Explicit Context Caching**: Integrated `ContextCacheConfig` with a 1-hour TTL and 2048-token threshold for significant cost savings on repeatable code audits.
- **Static Instruction Pattern**: Implemented the `static_instruction` split to maximize cache hit rates for persona and rules.
- **Resumability & Fault Tolerance**: Enabled `ResumabilityConfig` to allow long-running MAS audits to pause and resume without losing session state.
- **History Compaction**: Integrated `EventsCompactionConfig` to prevent "State Bloat" by automatically summarizing internal reasoning every 10 sub-invocations.
- **MAS Reasoning Engine**: Added `BuiltInPlanner` with `ThinkingConfig` for deeper architectural planning during audits.
- **Comprehensive Unit Testing**: Established a full testing suite in `tests/unit` covering:
    - Agent & App initialization.
    - Framework-specific resource efficiency heuristics (ADK, LangGraph, CrewAI).
    - Milestone-based metric estimation (Tokens, ROI).
    - Technical URL parsing and scraping (with BeautifulSoup mocks).

### Changed
- **Model Upgrade**: Upgraded core reasoning engine to **Gemini 2.5 Flash** for superior speed, efficiency, and context window utilization.
- **Core Refactoring**: Optimized internal imports for ADK 1.23+ compliance.
- **Enhanced Grounding**: Updated core instructions to leverage knowledge of new ADK memory features.

### Fixed
- **Backward Compatibility**: Restored `root_agent` alias for CLI discovery and project script stability.
- **Lazy Imports**: Refactored framework tools to use lazy imports for `beautifulsoup4`, ensuring stability in restricted environments.
