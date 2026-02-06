from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
"'compute_rate_move_probability' tool for FOMC Research sample agent."
import logging
from google.adk.tools import ToolContext
from ..shared_libraries import price_utils
logger = logging.getLogger(__name__)

def compute_rate_move_probability_tool(tool_context: ToolContext) -> dict[str, str]:
    """Computes the probabilities of rate moves for the requested meeting date.

    Args:
      tool_context: ToolContext object.

    Returns:
      A dict with "status" and (optional) "error_message" keys.
    """
    meeting_date = tool_context.state['requested_meeting_date']
    logger.debug('Computing rate move probabilities for %s', meeting_date)
    prob_result = price_utils.compute_probabilities(meeting_date)
    if prob_result['status'] != 'OK':
        return {'status': 'ERROR', 'message': prob_result['message']}
    probs = prob_result['output']
    logger.debug('Rate move probabilities: %s', probs)
    tool_context.state.update({'rate_move_probabilities': probs})
    return {'status': 'OK'}