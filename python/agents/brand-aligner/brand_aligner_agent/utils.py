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
import io
import json
import logging
import os
import re
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from google import genai
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse
from .models import AssetEvaluation
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)
matplotlib.use('Agg')
PROJECT_ID = os.getenv('PROJECT_ID') or os.getenv('GOOGLE_CLOUD_PROJECT')
LOCATION = os.getenv('LOCATION') or os.getenv('GOOGLE_CLOUD_LOCATION')
MODEL_NAME = os.getenv('MODEL_NAME')
RADAR_CHART_GROUPING_PROMPT = '\nYou are a data visualization expert. You are given a list of several criterion categories extracted from brand guidelines.\nYour task is to group these categories into a maximum of 10 high-level "Master Categories" suitable for a radar chart.\n\n**Instructions:**\n1.  Review the input list of categories.\n2.  Map each input category to a corresponding Master Category based on thematic similarity. Do not create new categories; only use those present in the input and potentially reword them if necessary. Remember, the goal is to reduce the number of categories to 10 or fewer.\n3.  Return a JSON object where the keys are the input categories and the values are the corresponding Master Categories. Your output MUST be a single JSON object. Do not include any other text or explanations\nbefore or after the JSON.\n\n**Input Categories:**\n{categories}\n\n**Output JSON:**\n'

def _text_progress_bar(percent: float, length: int=20) -> str:
    """Generates a compact text-based progress bar."""
    max_progress = 100
    if not (0 <= percent <= max_progress and isinstance(length, int) and (length > 0)):
        logger.error('Invalid percent or length for progress bar')
        if percent < 0:
            percent = 0
        elif percent > max_progress:
            percent = max_progress
        if not isinstance(length, int) or length < 0:
            length = 20
    filled_len = int(length * percent / max_progress)
    return f"[{'█' * filled_len}{'░' * (length - filled_len)}]"

def after_model_callback(callback_context: CallbackContext, llm_response: LlmResponse) -> LlmResponse | None:
    """Appends a progress bar to the agent's response."""
    original_text = ''
    if llm_response.content and llm_response.content.parts:
        for part in llm_response.content.parts:
            if part.text:
                original_text = part.text
                break
        if not original_text:
            return None
    else:
        return None
    state = callback_context.session.state
    guideline_files = state.get('guideline_files', [])
    asset_files = state.get('asset_files', [])
    processed_guidelines = state.get('processed_guidelines', [])
    evaluation_results = state.get('evaluation_results', [])
    num_guidelines = len(guideline_files)
    num_assets = len(asset_files)
    num_processed_guidelines = len(processed_guidelines)
    num_evaluated_assets = len(evaluation_results)
    total_weight = num_guidelines * 1 + num_assets * 2
    current_weight = num_processed_guidelines * 1 + num_evaluated_assets * 2
    progress = 0
    if total_weight > 0:
        progress = current_weight / total_weight * 100
    progress = min(progress, 100)
    if callback_context.agent_name == 'summarizer_agent':
        progress = 100
    prog_bar = _text_progress_bar(progress, 30)
    update = f'\n{prog_bar}\n\n{original_text}\n'
    for part in llm_response.content.parts:
        if part.text:
            part.text = update
            break
    return None

async def generate_radar_chart(evaluation: AssetEvaluation) -> bytes | None:
    """Generates a detailed radar chart for the asset evaluation."""
    max_categories_for_chart = 10
    raw_categories = {verdict.category for gv in evaluation.guideline_verdicts for verdict in gv.verdicts if verdict.category and verdict.verdict.lower() != 'n/a'}
    if not raw_categories:
        return None
    category_mapping = {cat: cat for cat in raw_categories}
    if len(raw_categories) > max_categories_for_chart:
        try:
            logger.info('Grouping categories for radar chart using LLM... Current categories: %r', list(raw_categories))
            client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
            prompt = RADAR_CHART_GROUPING_PROMPT.format(categories=list(raw_categories))
            response = await client.aio.models.generate_content(model=MODEL_NAME, contents=prompt, config={'response_mime_type': 'application/json'})
            if response.parsed:
                if isinstance(response.parsed, dict):
                    category_mapping = response.parsed
                else:
                    category_mapping = json.loads(response.text)
            else:
                clean_text = re.sub('(.*```json|```.*)', '', response.text.strip(), flags=re.DOTALL)
                category_mapping = json.loads(clean_text)
            logger.info(f'Radar Chart Category Mapping: {category_mapping}')
        except Exception as e:
            logger.error(f'Error grouping categories for radar chart: {e}. Falling back to raw categories.')
    master_category_scores = {}
    for gv in evaluation.guideline_verdicts:
        for verdict in gv.verdicts:
            if verdict.category and verdict.verdict.lower() != 'n/a':
                score = 1.0 if verdict.verdict.lower() == verdict.gt_answer.lower() else 0.0
                master_cat = category_mapping.get(verdict.category)
                if master_cat not in master_category_scores:
                    master_category_scores[master_cat] = []
                master_category_scores[master_cat].append(score)
    if not master_category_scores:
        return None
    labels = []
    stats = []
    for label, scores in master_category_scores.items():
        labels.append(label)
        stats.append(np.mean(scores))
    num_vars = len(labels)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    stats += stats[:1]
    angles += angles[:1]
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={'polar': True})
    plt.xticks(angles[:-1], labels)
    ax.plot(angles, stats, color='blue', linewidth=2)
    ax.fill(angles, stats, color='blue', alpha=0.25)
    ax.set_ylim(0, 1.0)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(['0.2', '0.4', '0.6', '0.8', '1.0'], color='grey', size=7)
    ax.set_title(f'Evaluation: {evaluation.asset_name}', va='bottom')
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf.read()