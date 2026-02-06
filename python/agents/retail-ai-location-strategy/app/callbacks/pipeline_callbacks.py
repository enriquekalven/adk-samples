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
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
'Pipeline callbacks for logging, state tracking, and artifact management.\n\nThis module provides before/after callbacks for each agent in the\nLocation Strategy Pipeline. Callbacks handle:\n- Logging stage transitions\n- Tracking pipeline progress in state\n- Saving artifacts (JSON report, HTML report, infographic)\n'
import json
import logging
import re
import traceback
from datetime import datetime
from google.adk.agents.callback_context import CallbackContext
from google.genai import types
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('LocationStrategyPipeline')

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def before_market_research(callback_context: CallbackContext) -> types.Content | None:
    """Log start of market research phase and initialize pipeline tracking."""
    logger.info('=' * 60)
    logger.info('STAGE 1: MARKET RESEARCH - Starting')
    logger.info(f"  Target Location: {callback_context.state.get('target_location', 'Not set')}")
    logger.info(f"  Business Type: {callback_context.state.get('business_type', 'Not set')}")
    logger.info('=' * 60)
    callback_context.state['current_date'] = datetime.now().strftime('%Y-%m-%d')
    callback_context.state['pipeline_stage'] = 'market_research'
    callback_context.state['pipeline_start_time'] = datetime.now().isoformat()
    if 'stages_completed' not in callback_context.state:
        callback_context.state['stages_completed'] = []
    return None

def before_competitor_mapping(callback_context: CallbackContext) -> types.Content | None:
    """Log start of competitor mapping phase."""
    logger.info('=' * 60)
    logger.info('STAGE 2A: COMPETITOR MAPPING - Starting')
    logger.info('  Using Google Maps Places API for real competitor data...')
    logger.info('=' * 60)
    callback_context.state['current_date'] = datetime.now().strftime('%Y-%m-%d')
    callback_context.state['pipeline_stage'] = 'competitor_mapping'
    if 'competitor_analysis' not in callback_context.state:
        callback_context.state['competitor_analysis'] = 'Competitor data being collected via Google Maps API...'
    return None

def before_gap_analysis(callback_context: CallbackContext) -> types.Content | None:
    """Log start of gap analysis phase."""
    logger.info('=' * 60)
    logger.info('STAGE 2B: GAP ANALYSIS - Starting')
    logger.info('  Executing Python code for quantitative market analysis...')
    logger.info('=' * 60)
    callback_context.state['current_date'] = datetime.now().strftime('%Y-%m-%d')
    callback_context.state['pipeline_stage'] = 'gap_analysis'
    if 'gap_analysis' not in callback_context.state:
        callback_context.state['gap_analysis'] = 'Gap analysis being computed...'
    return None

def before_strategy_advisor(callback_context: CallbackContext) -> types.Content | None:
    """Log start of strategy synthesis phase."""
    logger.info('=' * 60)
    logger.info('STAGE 3: STRATEGY SYNTHESIS - Starting')
    logger.info('  Using extended reasoning with thinking mode...')
    logger.info('  Generating structured LocationIntelligenceReport...')
    logger.info('=' * 60)
    callback_context.state['current_date'] = datetime.now().strftime('%Y-%m-%d')
    callback_context.state['pipeline_stage'] = 'strategy_synthesis'
    return None

def before_report_generator(callback_context: CallbackContext) -> types.Content | None:
    """Log start of report generation phase."""
    logger.info('=' * 60)
    logger.info('STAGE 4: REPORT GENERATION - Starting')
    logger.info('  Generating McKinsey/BCG style HTML executive report...')
    logger.info('=' * 60)
    callback_context.state['current_date'] = datetime.now().strftime('%Y-%m-%d')
    callback_context.state['pipeline_stage'] = 'report_generation'
    return None

def before_infographic_generator(callback_context: CallbackContext) -> types.Content | None:
    """Log start of infographic generation phase."""
    logger.info('=' * 60)
    logger.info('STAGE 5: INFOGRAPHIC GENERATION - Starting')
    logger.info('  Calling Gemini image generation API...')
    logger.info('=' * 60)
    callback_context.state['current_date'] = datetime.now().strftime('%Y-%m-%d')
    callback_context.state['pipeline_stage'] = 'infographic_generation'
    return None

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def after_market_research(callback_context: CallbackContext) -> types.Content | None:
    """Log completion of market research and update tracking."""
    findings = callback_context.state.get('market_research_findings', '')
    findings_len = len(findings) if isinstance(findings, str) else 0
    logger.info(f'STAGE 1: COMPLETE - Market research findings: {findings_len} characters')
    stages = callback_context.state.get('stages_completed', [])
    stages.append('market_research')
    callback_context.state['stages_completed'] = stages
    return None

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def after_competitor_mapping(callback_context: CallbackContext) -> types.Content | None:
    """Log completion of competitor mapping."""
    analysis = callback_context.state.get('competitor_analysis', '')
    analysis_len = len(analysis) if isinstance(analysis, str) else 0
    logger.info(f'STAGE 2A: COMPLETE - Competitor analysis: {analysis_len} characters')
    stages = callback_context.state.get('stages_completed', [])
    stages.append('competitor_mapping')
    callback_context.state['stages_completed'] = stages
    return None

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def after_gap_analysis(callback_context: CallbackContext) -> types.Content | None:
    """Log completion of gap analysis and extract executed Python code."""
    gap = callback_context.state.get('gap_analysis', '')
    gap_len = len(gap) if isinstance(gap, str) else 0
    logger.info(f'STAGE 2B: COMPLETE - Gap analysis: {gap_len} characters')
    extracted_code = _extract_python_code_from_content(gap)
    if not extracted_code:
        extracted_code = _extract_code_from_invocation(callback_context)
    if extracted_code:
        callback_context.state['gap_analysis_code'] = extracted_code
        logger.info(f'  Extracted Python code: {len(extracted_code)} characters')
    else:
        logger.info('  No Python code blocks found to extract')
    stages = callback_context.state.get('stages_completed', [])
    stages.append('gap_analysis')
    callback_context.state['stages_completed'] = stages
    return None

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def _extract_code_from_invocation(callback_context: CallbackContext) -> str:
    """Extract Python code from invocation context session events."""
    code_blocks = []
    try:
        invocation = getattr(callback_context, '_invocation_context', None) or getattr(callback_context, 'invocation_context', None)
        if not invocation:
            logger.debug('No invocation context available')
            return ''
        session = getattr(invocation, 'session', None)
        if not session:
            logger.debug('No session in invocation context')
            return ''
        events = getattr(session, 'events', None) or []
        logger.debug(f'Found {len(events)} events in session')
        for event in events:
            content = getattr(event, 'content', None)
            if not content:
                continue
            parts = getattr(content, 'parts', None) or []
            for part in parts:
                exec_code = getattr(part, 'executable_code', None)
                if exec_code:
                    code = getattr(exec_code, 'code', None)
                    if code and code.strip():
                        code_blocks.append(code.strip())
                        logger.debug(f'Found executable_code: {len(code)} chars')
        if code_blocks:
            logger.info(f'  Found {len(code_blocks)} code blocks from session events')
    except Exception as e:
        logger.warning(f'Error extracting code from invocation context: {e}')
        logger.debug(traceback.format_exc())
    return '\n\n# --- Next Code Block ---\n\n'.join(code_blocks)

def _extract_python_code_from_content(content: str) -> str:
    """Extract Python code blocks from markdown content."""
    if not content:
        return ''
    code_blocks = []
    pattern = '```(?:python|py)\\s*\\n(.*?)```'
    matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
    for match in matches:
        code = match.strip()
        if code:
            code_blocks.append(code)
    return '\n\n# ---\n\n'.join(code_blocks)

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def after_strategy_advisor(callback_context: CallbackContext) -> types.Content | None:
    """Log completion and save JSON artifact."""
    report = callback_context.state.get('strategic_report', {})
    logger.info('STAGE 3: COMPLETE - Strategic report generated')
    if report:
        try:
            if hasattr(report, 'model_dump'):
                report_dict = report.model_dump()
            else:
                report_dict = report
            json_str = json.dumps(report_dict, indent=2, default=str)
            json_artifact = types.Part.from_bytes(data=json_str.encode('utf-8'), mime_type='application/json')
            callback_context.save_artifact('intelligence_report.json', json_artifact)
            logger.info('  Saved artifact: intelligence_report.json')
        except Exception as e:
            logger.warning(f'  Failed to save JSON artifact: {e}')
    stages = callback_context.state.get('stages_completed', [])
    stages.append('strategy_synthesis')
    callback_context.state['stages_completed'] = stages
    return None

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def after_report_generator(callback_context: CallbackContext) -> types.Content | None:
    """Log completion of report generation.

    Note: The artifact is now saved directly in the generate_html_report tool
    using tool_context.save_artifact(). This callback just logs completion.
    """
    logger.info('STAGE 4: COMPLETE - HTML report generation finished')
    logger.info('  (Artifact saved directly by generate_html_report tool)')
    stages = callback_context.state.get('stages_completed', [])
    stages.append('report_generation')
    callback_context.state['stages_completed'] = stages
    return None

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def after_infographic_generator(callback_context: CallbackContext) -> types.Content | None:
    """Log completion of infographic generation.

    Note: The artifact is now saved directly in the generate_infographic tool
    using tool_context.save_artifact(). This callback just logs completion.
    """
    logger.info('STAGE 5: COMPLETE - Infographic generation finished')
    logger.info('  (Artifact saved directly by generate_infographic tool)')
    stages = callback_context.state.get('stages_completed', [])
    stages.append('infographic_generation')
    callback_context.state['stages_completed'] = stages
    logger.info('=' * 60)
    logger.info('PIPELINE COMPLETE')
    logger.info(f'  Stages completed: {stages}')
    logger.info(f'  Total stages: {len(stages)}/7')
    logger.info('=' * 60)
    return None