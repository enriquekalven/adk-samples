from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
'Performs quality assurance checks on generated media using a generative\nmodel.'
import logging
from typing import Literal
from google import genai
from google.api_core import exceptions as api_exceptions
from google.genai import types
from pydantic import BaseModel
from content_gen_agent.utils.evaluation_prompts import get_image_evaluation_prompt
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
EVALUATION_MODEL = 'gemini-3-flash-preview'

class EvalResult(BaseModel):
    """Represents the structured result of a media evaluation."""
    decision: Literal['Pass', 'Fail']
    reason: str
    subject_adherence: Literal['Pass', 'Fail']
    attribute_matching: Literal['Pass', 'Fail']
    spatial_accuracy: Literal['Pass', 'Fail']
    style_fidelity: Literal['Pass', 'Fail']
    quality_and_coherence: Literal['Pass', 'Fail']
    no_storyboard: Literal['Pass', 'Fail']

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def _get_internal_prompt(mime_type: str, evaluation_criteria: str) -> str:
    """Constructs the internal prompt for the evaluation model.

    Args:
        mime_type: The MIME type of the media being evaluated.
        evaluation_criteria: The specific criteria for evaluation.

    Returns:
        The formatted prompt string.
    """
    if mime_type == 'image/png':
        return get_image_evaluation_prompt(evaluation_criteria)
    return f"""\n    You are a strict Quality Assurance specialist.\n    Evaluate the following media based on this single criterion:\n    '{evaluation_criteria}'.\n\n    Your response must be in JSON.\n    - If the media passes, respond with: {{"decision": "Pass"}}\n    - If it fails, respond with:\n      {{"decision": "Fail", "reason": "A concise explanation."}}\n    """

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
async def evaluate_media(media_bytes: bytes, mime_type: str, evaluation_criteria: str) -> EvalResult | None:
    """Performs a quality assurance check on media bytes.

    Args:
        media_bytes: The media content as bytes.
        mime_type: The MIME type of the media.
        evaluation_criteria: The rule or question to evaluate media against.

    Returns:
        An instance of EvalResult, or None on failure.
    """
    try:
        client = genai.Client()
        internal_prompt = _get_internal_prompt(mime_type, evaluation_criteria)
        response = await client.aio.models.generate_content(model=EVALUATION_MODEL, contents=[internal_prompt, types.Part.from_bytes(data=media_bytes, mime_type=mime_type)], config=types.GenerateContentConfig(response_mime_type='application/json', response_schema=EvalResult))
        result = response.parsed
        logging.info('Overall Evaluation Decision: %s', result.decision)
        if result.decision == 'Fail':
            logging.warning('Evaluation failed reason: %s', result.reason)
        return result
    except (api_exceptions.GoogleAPICallError, ValueError) as e:
        logging.error('Media evaluation failed: %s', e, exc_info=True)
        return None

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def calculate_evaluation_score(evaluation_result: EvalResult | None) -> int:
    """Calculates a score based on the evaluation result.

    Args:
        evaluation_result: The result of the media evaluation.

    Returns:
        An integer score from 0 to 22.
    """
    if not evaluation_result:
        return 0
    score = 0
    score_mapping = {'decision': 10, 'subject_adherence': 2, 'attribute_matching': 2, 'spatial_accuracy': 2, 'style_fidelity': 2, 'quality_and_coherence': 2, 'no_storyboard': 2}
    for field, value in score_mapping.items():
        if getattr(evaluation_result, field) == 'Pass':
            score += value
    return score