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
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
import os
import warnings
from arize.otel import register
from dotenv import load_dotenv
from openinference.instrumentation.google_adk import GoogleADKInstrumentor
from opentelemetry import trace
load_dotenv()

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def instrument_adk_with_arize() -> trace.Tracer:
    """Instrument the ADK with Arize."""
    if os.getenv('ARIZE_SPACE_ID') is None:
        warnings.warn('ARIZE_SPACE_ID is not set', stacklevel=2)
        return None
    if os.getenv('ARIZE_API_KEY') is None:
        warnings.warn('ARIZE_API_KEY is not set', stacklevel=2)
        return None
    tracer_provider = register(space_id=os.getenv('ARIZE_SPACE_ID'), api_key=os.getenv('ARIZE_API_KEY'), project_name=os.getenv('ARIZE_PROJECT_NAME', 'adk-rag-agent'))
    GoogleADKInstrumentor().instrument(tracer_provider=tracer_provider)
    return tracer_provider.get_tracer(__name__)