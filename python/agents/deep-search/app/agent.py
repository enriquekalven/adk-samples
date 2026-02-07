# Copyright 2025 Google LLC
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

from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from google.adk.agents.context_cache_config import ContextCacheConfig
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
import datetime
import logging
import re
from collections.abc import AsyncGenerator
from typing import Literal
from google.adk.agents import BaseAgent, LlmAgent, LoopAgent, SequentialAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.invocation_context import InvocationContext
from google.adk.apps.app import App
from google.adk.events import Event, EventActions
from google.adk.planners import BuiltInPlanner
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool
from google.genai import types as genai_types
from pydantic import BaseModel, Field
from .config import config

class SearchQuery(BaseModel):
    """Model representing a specific search query for web search."""
    search_query: str = Field(description='A highly specific and targeted query for web search.')

class Feedback(BaseModel):
    """Model for providing evaluation feedback on research quality."""
    grade: Literal['pass', 'fail'] = Field(description="Evaluation result. 'pass' if the research is sufficient, 'fail' if it needs revision.")
    comment: str = Field(description='Detailed explanation of the evaluation, highlighting strengths and/or weaknesses of the research.')
    follow_up_queries: list[SearchQuery] | None = Field(default=None, description="A list of specific, targeted follow-up search queries needed to fix research gaps. This should be null or empty if the grade is 'pass'.")

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def collect_research_sources_callback(callback_context: CallbackContext) -> None:
    """Collects and organizes web-based research sources and their supported claims from agent events.

    This function processes the agent's `session.events` to extract web source details (URLs,
    titles, domains from `grounding_chunks`) and associated text segments with confidence scores
    (from `grounding_supports`). The aggregated source information and a mapping of URLs to short
    IDs are cumulatively stored in `callback_context.state`.

    Args:
        callback_context (CallbackContext): The context object providing access to the agent's
            session events and persistent state.
    """
    session = callback_context._invocation_context.session
    url_to_short_id = callback_context.state.get('url_to_short_id', {})
    sources = callback_context.state.get('sources', {})
    id_counter = len(url_to_short_id) + 1
    for event in session.events:
        if not (event.grounding_metadata and event.grounding_metadata.grounding_chunks):
            continue
        chunks_info = {}
        for idx, chunk in enumerate(event.grounding_metadata.grounding_chunks):
            if not chunk.web:
                continue
            url = chunk.web.uri
            title = chunk.web.title if chunk.web.title != chunk.web.domain else chunk.web.domain
            if url not in url_to_short_id:
                short_id = f'src-{id_counter}'
                url_to_short_id[url] = short_id
                sources[short_id] = {'short_id': short_id, 'title': title, 'url': url, 'domain': chunk.web.domain, 'supported_claims': []}
                id_counter += 1
            chunks_info[idx] = url_to_short_id[url]
        if event.grounding_metadata.grounding_supports:
            for support in event.grounding_metadata.grounding_supports:
                confidence_scores = support.confidence_scores or []
                chunk_indices = support.grounding_chunk_indices or []
                for i, chunk_idx in enumerate(chunk_indices):
                    if chunk_idx in chunks_info:
                        short_id = chunks_info[chunk_idx]
                        confidence = confidence_scores[i] if i < len(confidence_scores) else 0.5
                        text_segment = support.segment.text if support.segment else ''
                        sources[short_id]['supported_claims'].append({'text_segment': text_segment, 'confidence': confidence})
    callback_context.state['url_to_short_id'] = url_to_short_id
    callback_context.state['sources'] = sources

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def citation_replacement_callback(callback_context: CallbackContext) -> genai_types.Content:
    """Replaces citation tags in a report with Markdown-formatted links.

    Processes 'final_cited_report' from context state, converting tags like
    `<cite source="src-N"/>` into hyperlinks using source information from
    `callback_context.state["sources"]`. Also fixes spacing around punctuation.

    Args:
        callback_context (CallbackContext): Contains the report and source information.

    Returns:
        genai_types.Content: The processed report with Markdown citation links.
    """
    final_report = callback_context.state.get('final_cited_report', '')
    sources = callback_context.state.get('sources', {})

    def tag_replacer(match: re.Match) -> str:
        short_id = match.group(1)
        if not (source_info := sources.get(short_id)):
            logging.warning(f'Invalid citation tag found and removed: {match.group(0)}')
            return ''
        display_text = source_info.get('title', source_info.get('domain', short_id))
        return f" [{display_text}]({source_info['url']})"
    processed_report = re.sub('<cite\\s+source\\s*=\\s*["\\\']?\\s*(src-\\d+)\\s*["\\\']?\\s*/>', tag_replacer, final_report)
    processed_report = re.sub('\\s+([.,;:])', '\\1', processed_report)
    callback_context.state['final_report_with_citations'] = processed_report
    return genai_types.Content(parts=[genai_types.Part(text=processed_report)])

class EscalationChecker(BaseAgent):
    """Checks research evaluation and escalates to stop the loop if grade is 'pass'."""

    def __init__(self, name: str):
        super().__init__(name=name)

    @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        evaluation_result = ctx.session.state.get('research_evaluation')
        if evaluation_result and evaluation_result.get('grade') == 'pass':
            logging.info(f'[{self.name}] Research evaluation passed. Escalating to stop loop.')
            yield Event(author=self.name, actions=EventActions(escalate=True))
        else:
            logging.info(f'[{self.name}] Research evaluation failed or not found. Loop will continue.')
            yield Event(author=self.name)
plan_generator = LlmAgent(model=config.worker_model, name='plan_generator', description='Generates or refine the existing 5 line action-oriented research plan, using minimal search only for topic clarification.', instruction=f"""\n    You are a research strategist. Your job is to create a high-level RESEARCH PLAN, not a summary. If there is already a RESEARCH PLAN in the session state,\n    improve upon it based on the user feedback.\n\n    RESEARCH PLAN(SO FAR):\n    {{ research_plan? }}\n\n    **GENERAL INSTRUCTION: CLASSIFY TASK TYPES**\n    Your plan must clearly classify each goal for downstream execution. Each bullet point should start with a task type prefix:\n    - **`[RESEARCH]`**: For goals that primarily involve information gathering, investigation, analysis, or data collection (these require search tool usage by a researcher).\n    - **`[DELIVERABLE]`**: For goals that involve synthesizing collected information, creating structured outputs (e.g., tables, charts, summaries, reports), or compiling final output artifacts (these are executed AFTER research tasks, often without further search).\n\n    **INITIAL RULE: Your initial output MUST start with a bulleted list of 5 action-oriented research goals or key questions, followed by any *inherently implied* deliverables.**\n    - All initial 5 goals will be classified as `[RESEARCH]` tasks.\n    - A good goal for `[RESEARCH]` starts with a verb like "Analyze," "Identify," "Investigate."\n    - A bad output is a statement of fact like "The event was in April 2024."\n    - **Proactive Implied Deliverables (Initial):** If any of your initial 5 `[RESEARCH]` goals inherently imply a standard output or deliverable (e.g., a comparative analysis suggesting a comparison table, or a comprehensive review suggesting a summary document), you MUST add these as additional, distinct goals immediately after the initial 5. Phrase these as *synthesis or output creation actions* (e.g., "Create a summary," "Develop a comparison," "Compile a report") and prefix them with `[DELIVERABLE][IMPLIED]`.\n\n    **REFINEMENT RULE**:\n    - **Integrate Feedback & Mark Changes:** When incorporating user feedback, make targeted modifications to existing bullet points. Add `[MODIFIED]` to the existing task type and status prefix (e.g., `[RESEARCH][MODIFIED]`). If the feedback introduces new goals:\n        - If it's an information gathering task, prefix it with `[RESEARCH][NEW]`.\n        - If it's a synthesis or output creation task, prefix it with `[DELIVERABLE][NEW]`.\n    - **Proactive Implied Deliverables (Refinement):** Beyond explicit user feedback, if the nature of an existing `[RESEARCH]` goal (e.g., requiring a structured comparison, deep dive analysis, or broad synthesis) or a `[DELIVERABLE]` goal inherently implies an additional, standard output or synthesis step (e.g., a detailed report following a summary, or a visual representation of complex data), proactively add this as a new goal. Phrase these as *synthesis or output creation actions* and prefix them with `[DELIVERABLE][IMPLIED]`.\n    - **Maintain Order:** Strictly maintain the original sequential order of existing bullet points. New bullets, whether `[NEW]` or `[IMPLIED]`, should generally be appended to the list, unless the user explicitly instructs a specific insertion point.\n    - **Flexible Length:** The refined plan is no longer constrained by the initial 5-bullet limit and may comprise more goals as needed to fully address the feedback and implied deliverables.\n\n    **TOOL USE IS STRICTLY LIMITED:**\n    Your goal is to create a generic, high-quality plan *without searching*.\n    Only use `google_search` if a topic is ambiguous or time-sensitive and you absolutely cannot create a plan without a key piece of identifying information.\n    You are explicitly forbidden from researching the *content* or *themes* of the topic. That is the next agent's job. Your search is only to identify the subject, not to investigate it.\n    Current date: {datetime.datetime.now().strftime('%Y-%m-%d')}\n    """, tools=[google_search], context_cache_config=ContextCacheConfig(min_tokens=2048, ttl_seconds=600))
section_planner = LlmAgent(model=config.worker_model, name='section_planner', description='Breaks down the research plan into a structured markdown outline of report sections.', instruction='\n    You are an expert report architect. Using the research topic and the plan from the \'research_plan\' state key, design a logical structure for the final report.\n    Note: Ignore all the tag nanes ([MODIFIED], [NEW], [RESEARCH], [DELIVERABLE]) in the research plan.\n    Your task is to create a markdown outline with 4-6 distinct sections that cover the topic comprehensively without overlap.\n    You can use any markdown format you prefer, but here\'s a suggested structure:\n    # Section Name\n    A brief overview of what this section covers\n    Feel free to add subsections or bullet points if needed to better organize the content.\n    Make sure your outline is clear and easy to follow.\n    Do not include a "References" or "Sources" section in your outline. Citations will be handled in-line.\n    ', output_key='report_sections', context_cache_config=ContextCacheConfig(min_tokens=2048, ttl_seconds=600))
section_researcher = LlmAgent(model=config.worker_model, name='section_researcher', description='Performs the crucial first pass of web research.', planner=BuiltInPlanner(thinking_config=genai_types.ThinkingConfig(include_thoughts=True)), instruction='\n    You are a highly capable and diligent research and synthesis agent. Your comprehensive task is to execute a provided research plan with **absolute fidelity**, first by gathering necessary information, and then by synthesizing that information into specified outputs.\n\n    You will be provided with a sequential list of research plan goals, stored in the `research_plan` state key. Each goal will be clearly prefixed with its primary task type: `[RESEARCH]` or `[DELIVERABLE]`.\n\n    Your execution process must strictly adhere to these two distinct and sequential phases:\n\n    ---\n\n    **Phase 1: Information Gathering (`[RESEARCH]` Tasks)**\n\n    *   **Execution Directive:** You **MUST** systematically process every goal prefixed with `[RESEARCH]` before proceeding to Phase 2.\n    *   For each `[RESEARCH]` goal:\n        *   **Query Generation:** Formulate a comprehensive set of 4-5 targeted search queries. These queries must be expertly designed to broadly cover the specific intent of the `[RESEARCH]` goal from multiple angles.\n        *   **Execution:** Utilize the `google_search` tool to execute **all** generated queries for the current `[RESEARCH]` goal.\n        *   **Summarization:** Synthesize the search results into a detailed, coherent summary that directly addresses the objective of the `[RESEARCH]` goal.\n        *   **Internal Storage:** Store this summary, clearly tagged or indexed by its corresponding `[RESEARCH]` goal, for later and exclusive use in Phase 2. You **MUST NOT** lose or discard any generated summaries.\n\n    ---\n\n    **Phase 2: Synthesis and Output Creation (`[DELIVERABLE]` Tasks)**\n\n    *   **Execution Prerequisite:** This phase **MUST ONLY COMMENCE** once **ALL** `[RESEARCH]` goals from Phase 1 have been fully completed and their summaries are internally stored.\n    *   **Execution Directive:** You **MUST** systematically process **every** goal prefixed with `[DELIVERABLE]`. For each `[DELIVERABLE]` goal, your directive is to **PRODUCE** the artifact as explicitly described.\n    *   For each `[DELIVERABLE]` goal:\n        *   **Instruction Interpretation:** You will interpret the goal\'s text (following the `[DELIVERABLE]` tag) as a **direct and non-negotiable instruction** to generate a specific output artifact.\n            *   *If the instruction details a table (e.g., "Create a Detailed Comparison Table in Markdown format"), your output for this step **MUST** be a properly formatted Markdown table utilizing columns and rows as implied by the instruction and the prepared data.*\n            *   *If the instruction states to prepare a summary, report, or any other structured output, your output for this step **MUST** be that precise artifact.*\n        *   **Data Consolidation:** Access and utilize **ONLY** the summaries generated during Phase 1 (`[RESEARCH]` tasks`) to fulfill the requirements of the current `[DELIVERABLE]` goal. You **MUST NOT** perform new searches.\n        *   **Output Generation:** Based on the specific instruction of the `[DELIVERABLE]` goal:\n            *   Carefully extract, organize, and synthesize the relevant information from your previously gathered summaries.\n            *   Must always produce the specified output artifact (e.g., a concise summary, a structured comparison table, a comprehensive report, a visual representation, etc.) with accuracy and completeness.\n        *   **Output Accumulation:** Maintain and accumulate **all** the generated `[DELIVERABLE]` artifacts. These are your final outputs.\n\n    ---\n\n    **Final Output:** Your final output will comprise the complete set of processed summaries from `[RESEARCH]` tasks AND all the generated artifacts from `[DELIVERABLE]` tasks, presented clearly and distinctly.\n    ', tools=[google_search], output_key='section_research_findings', after_agent_callback=collect_research_sources_callback, context_cache_config=ContextCacheConfig(min_tokens=2048, ttl_seconds=600))
research_evaluator = LlmAgent(model=config.critic_model, name='research_evaluator', description='Critically evaluates research and generates follow-up queries.', instruction=f"""\n    You are a meticulous quality assurance analyst evaluating the research findings in 'section_research_findings'.\n\n    **CRITICAL RULES:**\n    1. Assume the given research topic is correct. Do not question or try to verify the subject itself.\n    2. Your ONLY job is to assess the quality, depth, and completeness of the research provided *for that topic*.\n    3. Focus on evaluating: Comprehensiveness of coverage, logical flow and organization, use of credible sources, depth of analysis, and clarity of explanations.\n    4. Do NOT fact-check or question the fundamental premise or timeline of the topic.\n    5. If suggesting follow-up queries, they should dive deeper into the existing topic, not question its validity.\n\n    Be very critical about the QUALITY of research. If you find significant gaps in depth or coverage, assign a grade of "fail",\n    write a detailed comment about what's missing, and generate 5-7 specific follow-up queries to fill those gaps.\n    If the research thoroughly covers the topic, grade "pass".\n\n    Current date: {datetime.datetime.now().strftime('%Y-%m-%d')}\n    Your response must be a single, raw JSON object validating against the 'Feedback' schema.\n    """, output_schema=Feedback, disallow_transfer_to_parent=True, disallow_transfer_to_peers=True, output_key='research_evaluation', context_cache_config=ContextCacheConfig(min_tokens=2048, ttl_seconds=600))
enhanced_search_executor = LlmAgent(model=config.worker_model, name='enhanced_search_executor', description='Executes follow-up searches and integrates new findings.', planner=BuiltInPlanner(thinking_config=genai_types.ThinkingConfig(include_thoughts=True)), instruction="\n    You are a specialist researcher executing a refinement pass.\n    You have been activated because the previous research was graded as 'fail'.\n\n    1.  Review the 'research_evaluation' state key to understand the feedback and required fixes.\n    2.  Execute EVERY query listed in 'follow_up_queries' using the 'google_search' tool.\n    3.  Synthesize the new findings and COMBINE them with the existing information in 'section_research_findings'.\n    4.  Your output MUST be the new, complete, and improved set of research findings.\n    ", tools=[google_search], output_key='section_research_findings', after_agent_callback=collect_research_sources_callback, context_cache_config=ContextCacheConfig(min_tokens=2048, ttl_seconds=600))
report_composer = LlmAgent(model=config.critic_model, name='report_composer_with_citations', include_contents='none', description='Transforms research data and a markdown outline into a final, cited report.', instruction='\n    Transform the provided data into a polished, professional, and meticulously cited research report.\n\n    ---\n    ### INPUT DATA\n    *   Research Plan: `{research_plan}`\n    *   Research Findings: `{section_research_findings}`\n    *   Citation Sources: `{sources}`\n    *   Report Structure: `{report_sections}`\n\n    ---\n    ### CRITICAL: Citation System\n    To cite a source, you MUST insert a special citation tag directly after the claim it supports.\n\n    **The only correct format is:** `<cite source="src-ID_NUMBER" />`\n\n    ---\n    ### Final Instructions\n    Generate a comprehensive report using ONLY the `<cite source="src-ID_NUMBER" />` tag system for all citations.\n    The final report must strictly follow the structure provided in the **Report Structure** markdown outline.\n    Do not include a "References" or "Sources" section; all citations must be in-line.\n    ', output_key='final_cited_report', after_agent_callback=citation_replacement_callback, context_cache_config=ContextCacheConfig(min_tokens=2048, ttl_seconds=600))
research_pipeline = SequentialAgent(name='research_pipeline', description='Executes a pre-approved research plan. It performs iterative research, evaluation, and composes a final, cited report.', sub_agents=[section_planner, section_researcher, LoopAgent(name='iterative_refinement_loop', max_iterations=config.max_search_iterations, sub_agents=[research_evaluator, EscalationChecker(name='escalation_checker'), enhanced_search_executor]), report_composer])
interactive_planner_agent = LlmAgent(name='interactive_planner_agent', model=config.worker_model, description='The primary research assistant. It collaborates with the user to create a research plan, and then executes it upon approval.', instruction=f"""\n    You are a research planning assistant. Your primary function is to convert ANY user request into a research plan.\n\n    **CRITICAL RULE: Never answer a question directly or refuse a request.** Your one and only first step is to use the `plan_generator` tool to propose a research plan for the user's topic.\n    If the user asks a question, you MUST immediately call `plan_generator` to create a plan to answer the question.\n\n    Your workflow is:\n    1.  **Plan:** Use `plan_generator` to create a draft plan and present it to the user.\n    2.  **Refine:** Incorporate user feedback until the plan is approved.\n    3.  **Execute:** Once the user gives EXPLICIT approval (e.g., "looks good, run it"), you MUST delegate the task to the `research_pipeline` agent, passing the approved plan.\n\n    Current date: {datetime.datetime.now().strftime('%Y-%m-%d')}\n    Do not perform any research yourself. Your job is to Plan, Refine, and Delegate.\n    """, sub_agents=[research_pipeline], tools=[AgentTool(plan_generator)], output_key='research_plan', context_cache_config=ContextCacheConfig(min_tokens=2048, ttl_seconds=600))
root_agent = interactive_planner_agent
app = App(root_agent=root_agent, name='app', context_cache_config=ContextCacheConfig(min_tokens=2048, ttl_seconds=600))