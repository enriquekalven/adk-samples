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
'Callback functions for FOMC Research Agent.'
import logging
import time
from typing import Any
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.invocation_context import InvocationContext
from google.adk.models import LlmRequest
from google.adk.sessions.state import State
from google.adk.tools import BaseTool
from google.adk.tools.tool_context import ToolContext
from jsonschema import ValidationError
from customer_service.entities.customer import Customer
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
RATE_LIMIT_SECS = 60
RPM_QUOTA = 10
MAX_DISCOUNT_RATE = 10

def rate_limit_callback(callback_context: CallbackContext, llm_request: LlmRequest) -> None:
    """Callback function that implements a query rate limit.

    Args:
      callback_context: A CallbackContext obj representing the active callback
        context.
      llm_request: A LlmRequest obj representing the active LLM request.
    """
    for content in llm_request.contents:
        for part in content.parts:
            if part.text == '':
                part.text = ' '
    now = time.time()
    if 'timer_start' not in callback_context.state:
        callback_context.state['timer_start'] = now
        callback_context.state['request_count'] = 1
        logger.debug('rate_limit_callback [timestamp: %i, req_count: 1, elapsed_secs: 0]', now)
        return
    request_count = callback_context.state['request_count'] + 1
    elapsed_secs = now - callback_context.state['timer_start']
    logger.debug('rate_limit_callback [timestamp: %i, request_count: %i, elapsed_secs: %i]', now, request_count, elapsed_secs)
    if request_count > RPM_QUOTA:
        delay = RATE_LIMIT_SECS - elapsed_secs + 1
        if delay > 0:
            logger.debug('Sleeping for %i seconds', delay)
            time.sleep(delay)
        callback_context.state['timer_start'] = now
        callback_context.state['request_count'] = 1
    else:
        callback_context.state['request_count'] = request_count
    return

def validate_customer_id(customer_id: str, session_state: State) -> tuple[bool, str]:
    """
    Validates the customer ID against the customer profile in the session state.

    Args:
        customer_id (str): The ID of the customer to validate.
        session_state (State): The session state containing the customer profile.

    Returns:
        A tuple containing an bool (True/False) and a String.
        When False, a string with the error message to pass to the model for deciding
        what actions to take to remediate.
    """
    if 'customer_profile' not in session_state:
        return (False, 'No customer profile selected. Please select a profile.')
    try:
        c = Customer.model_validate_json(session_state['customer_profile'])
        if customer_id == c.customer_id:
            return (True, None)
        else:
            return (False, 'You cannot use the tool with customer_id ' + customer_id + ', only for ' + c.customer_id + '.')
    except ValidationError:
        return (False, "Customer profile couldn't be parsed. Please reload the customer data. ")

def lowercase_value(value):
    """Make dictionary lowercase"""
    if isinstance(value, dict):
        return (dict(k, lowercase_value(v)) for k, v in value.items())
    elif isinstance(value, str):
        return value.lower()
    elif isinstance(value, (list, set, tuple)):
        tp = type(value)
        return tp((lowercase_value(i) for i in value))
    else:
        return value

def before_tool(tool: BaseTool, args: dict[str, Any], tool_context: CallbackContext):
    lowercase_value(args)
    if 'customer_id' in args:
        valid, err = validate_customer_id(args['customer_id'], tool_context.state)
        if not valid:
            return err
    if tool.name == 'sync_ask_for_approval':
        amount = args.get('value', None)
        if amount <= MAX_DISCOUNT_RATE:
            return {'status': 'approved', 'message': 'You can approve this discount; no manager needed.'}
    if tool.name == 'modify_cart':
        if args.get('items_added') is True and args.get('items_removed') is True:
            return {'result': 'I have added and removed the requested items.'}
    return None

def after_tool(tool: BaseTool, args: dict[str, Any], tool_context: ToolContext, tool_response: dict) -> dict | None:
    if tool.name == 'sync_ask_for_approval':
        if tool_response['status'] == 'approved':
            logger.debug('Applying discount to the cart')
    if tool.name == 'approve_discount':
        if tool_response['status'] == 'ok':
            logger.debug('Applying discount to the cart')
    return None

def before_agent(callback_context: InvocationContext):
    if 'customer_profile' not in callback_context.state:
        callback_context.state['customer_profile'] = Customer.get_customer('123').to_json()