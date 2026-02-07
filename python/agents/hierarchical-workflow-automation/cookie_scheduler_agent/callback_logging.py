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
import logging
import google.cloud.logging
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse

def log_query_to_model(callback_context: CallbackContext, llm_request: LlmRequest):
    cloud_logging_client = google.cloud.logging.Client()
    cloud_logging_client.setup_logging()
    if llm_request.contents and llm_request.contents[-1].role == 'user':
        if llm_request.contents[-1].parts and 'text' in llm_request.contents[-1].parts:
            last_user_message = llm_request.contents[-1].parts[0].text
            logging.info(f'[query to {callback_context.agent_name}]: ' + last_user_message)

def log_model_response(callback_context: CallbackContext, llm_response: LlmResponse):
    cloud_logging_client = google.cloud.logging.Client()
    cloud_logging_client.setup_logging()
    if llm_response.content and llm_response.content.parts:
        for part in llm_response.content.parts:
            if part.text:
                logging.info(f'[response from {callback_context.agent_name}]: ' + part.text)
            elif part.function_call:
                logging.info(f'[function call from {callback_context.agent_name}]: ' + part.function_call.name)