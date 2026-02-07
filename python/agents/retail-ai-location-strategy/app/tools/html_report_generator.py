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

from google.adk.agents.context_cache_config import ContextCacheConfig
'HTML Report Generator tool for creating executive reports.\n\nUses direct text generation (same as original notebook Part 4) to create\nMcKinsey/BCG style 7-slide HTML presentations from strategic report data.\nSaves the generated HTML as an artifact for download in adk web.\n'
import logging
from datetime import datetime
from google import genai
from google.adk.tools import ToolContext
from google.genai import types
from google.genai.errors import ServerError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from ..config import PRO_MODEL
logger = logging.getLogger('LocationStrategyPipeline')

async def generate_html_report(report_data: str, tool_context: ToolContext) -> dict:
    """Generate a McKinsey/BCG style HTML executive report and save as artifact.

    This tool creates a professional 7-slide HTML presentation from the
    location intelligence report data using direct text generation with Gemini.
    The generated HTML is automatically saved as an artifact for viewing in adk web.

    Args:
        report_data: The strategic report data in a formatted string containing
                    analysis overview, top recommendation, competition metrics,
                    market characteristics, alternatives, insights, and methodology.
        tool_context: ADK ToolContext for saving artifacts.

    Returns:
        dict: A dictionary containing:
            - status: "success" or "error"
            - message: Status message
            - artifact_filename: Name of saved artifact (if successful)
            - artifact_version: Version number of artifact (if successful)
            - html_length: Character count of generated HTML
            - error_message: Error details (if failed)
    """
    try:
        client = genai.Client()
        current_date = datetime.now().strftime('%Y-%m-%d')
        prompt = f'Generate a comprehensive, professional HTML report for a location intelligence analysis.\n\nThis report should be in the style of McKinsey/BCG consulting presentations:\n- Multi-slide format using full-screen scrollable sections\n- Modern, clean, executive-ready design\n- Data-driven visualizations\n- Professional color scheme and typography\n\nCRITICAL REQUIREMENTS:\n\n1. STRUCTURE - Create 7 distinct slides (full-screen sections):\n\n   SLIDE 1 - EXECUTIVE SUMMARY & TOP RECOMMENDATION\n   - Large, prominent display of recommended location and score\n   - Business type and target location\n   - High-level market validation\n   - Eye-catching hero section\n\n   SLIDE 2 - TOP RECOMMENDATION DETAILS\n   - All strengths with evidence (cards/boxes)\n   - All concerns with mitigation strategies\n   - Opportunity type and target customer segment\n\n   SLIDE 3 - COMPETITION ANALYSIS\n   - Competition metrics (total competitors, density, chain dominance)\n   - Visual representation of key numbers (large stat boxes)\n   - Average ratings, high performers count\n\n   SLIDE 4 - MARKET CHARACTERISTICS\n   - Population density, income level, infrastructure\n   - Foot traffic patterns, rental costs\n   - Grid/card layout for each characteristic\n\n   SLIDE 5 - ALTERNATIVE LOCATIONS\n   - Each alternative in a comparison card\n   - Scores, opportunity types, strengths/concerns\n   - Why each is not the top choice\n\n   SLIDE 6 - KEY INSIGHTS & NEXT STEPS\n   - Strategic insights (bullet points or cards)\n   - Actionable next steps (numbered list)\n\n   SLIDE 7 - METHODOLOGY\n   - How the analysis was performed\n   - Data sources and approach\n\n2. DESIGN:\n   - Use professional consulting color palette:\n     * Primary: Navy blue (#1e3a8a, #3b82f6) for headers/trust\n     * Success: Green (#059669, #10b981) for positive metrics\n     * Warning: Amber (#d97706, #f59e0b) for concerns\n     * Neutral: Grays (#6b7280, #e5e7eb) for backgrounds\n   - Modern sans-serif fonts (system: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto)\n   - Cards with subtle shadows and rounded corners\n   - Generous white space and padding\n   - Responsive grid layouts\n\n3. TECHNICAL:\n   - Self-contained: ALL CSS embedded in <style> tag\n   - No external dependencies (no CDNs, no external images)\n   - Each slide: min-height: 100vh; page-break-after: always;\n   - Smooth scroll behavior\n   - Print-friendly\n\n4. DATA TO INCLUDE (use EXACTLY this data, do not invent):\n\n{report_data}\n\n5. OUTPUT:\n   - Generate ONLY the complete HTML code\n   - Start with <!DOCTYPE html>\n   - End with </html>\n   - NO explanations before or after the HTML\n   - NO markdown code fences\n\nMake it visually stunning, data-rich, and executive-ready.\n\nCurrent date: {current_date}\n'
        logger.info('Generating HTML report using Gemini...')

        @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=30), retry=retry_if_exception_type(ServerError), before_sleep=lambda retry_state: logger.warning(f'Gemini API error, retrying in {retry_state.next_action.sleep} seconds... (attempt {retry_state.attempt_number}/3)'))
        def generate_with_retry():
            return client.models.generate_content(model=PRO_MODEL, contents=prompt, config=types.GenerateContentConfig(temperature=1.0))
        response = generate_with_retry()
        html_code = response.text
        if html_code.startswith('```'):
            if html_code.startswith('```html'):
                html_code = html_code[7:]
            elif html_code.startswith('```HTML'):
                html_code = html_code[7:]
            else:
                html_code = html_code[3:]
            if html_code.rstrip().endswith('```'):
                html_code = html_code.rstrip()[:-3]
            html_code = html_code.strip()
        if not html_code.strip().startswith('<!DOCTYPE') and (not html_code.strip().startswith('<html')):
            logger.warning('Generated content may not be valid HTML')
        html_artifact = types.Part.from_bytes(data=html_code.encode('utf-8'), mime_type='text/html')
        artifact_filename = 'executive_report.html'
        version = await tool_context.save_artifact(filename=artifact_filename, artifact=html_artifact)
        tool_context.state['html_report_content'] = html_code
        logger.info(f'Saved HTML report artifact: {artifact_filename} (version {version})')
        return {'status': 'success', 'message': f"HTML report generated and saved as artifact '{artifact_filename}'", 'artifact_filename': artifact_filename, 'artifact_version': version, 'html_length': len(html_code)}
    except Exception as e:
        logger.error(f'Failed to generate HTML report: {e}')
        return {'status': 'error', 'error_message': f'Failed to generate HTML report: {e!s}'}