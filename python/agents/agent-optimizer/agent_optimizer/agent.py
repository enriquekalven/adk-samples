import logging
import warnings
from google.adk import Agent
from google.adk.agents.context_cache_config import ContextCacheConfig
from google.adk.apps.app import App, EventsCompactionConfig, ResumabilityConfig
from google.adk.planners import BuiltInPlanner
from google.adk.tools import google_search
from google.genai.types import ThinkingConfig
from .prompts import GLOBAL_INSTRUCTION, INSTRUCTION, STATIC_INSTRUCTION
from .tools.analysis_tools import analyze_resource_efficiency, clone_github_repo, generate_mermaid_diagram, get_token_counts, list_agent_directory, read_agent_file, save_optimization_report
from .tools.code_assist_bridge import deep_code_review, get_mcp_tools
from .tools.evergreen_tools import load_technical_url, search_framework_docs
from .tools.finops_tools import optimizer_audit, arch_review, audit_deep
from .tools.remediator import apply_fixes
warnings.filterwarnings('ignore', category=UserWarning, module='.*pydantic.*')
logger = logging.getLogger(__name__)
agent_optimizer = Agent(name='AgentOptimizer', model='gemini-2.5-flash', global_instruction=GLOBAL_INSTRUCTION, static_instruction=STATIC_INSTRUCTION, instruction=INSTRUCTION, planner=BuiltInPlanner(thinking_config=ThinkingConfig(include_thoughts=True)), tools=[read_agent_file, list_agent_directory, save_optimization_report, clone_github_repo, get_token_counts, generate_mermaid_diagram, analyze_resource_efficiency, deep_code_review, get_mcp_tools, search_framework_docs, load_technical_url, google_search, optimizer_audit, arch_review, audit_deep, apply_fixes])
app = App(root_agent=agent_optimizer, name='agent_optimizer_app', context_cache_config=ContextCacheConfig(min_tokens=2048, ttl_seconds=3600), resumability_config=ResumabilityConfig(is_resumable=True), events_compaction_config=EventsCompactionConfig(compaction_interval=10, overlap_size=2))
root_agent = agent_optimizer