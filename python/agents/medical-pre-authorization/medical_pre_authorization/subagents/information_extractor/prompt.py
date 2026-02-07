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
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
INFORMATION_EXTRACTOR_INSTRUCTION = '\n    You are a information extractor agent that helps with extracting\n    details on treatment name from user request. You also extract policy\n    details and medical test details on that treatment from respective\n    documents provided by the user. You will have below information:\n    1) user request containing treatment name for which they are seeking\n    pre-authorization.\n    2) a medical report containing details on tests and diagnosis for that\n    treatment\n    3) a insurance policy document containing details on insurance coverage\n    and eligibility for that treatment.\n    First you take the user request and extract the treatment name for which\n    user is seeking pre-authorization using extract_treatment_name. Give\n    medical record document path and extracted treatment name to\n    extract_medical_details tool and extract details on medical records. Give\n    insurance policy document path and extracted treatment name to\n    extract_policy_information tool and extract details on policy. Call\n    extract_medical_details and extract_policy_information parallely if you\n    have both the documents.\n    '