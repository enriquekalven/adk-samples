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

import os
GCS_BUCKET_NAME = os.getenv('GCS_BUCKET_NAME')
SCORE_THRESHOLD = int(os.getenv('SCORE_THRESHOLD', '45'))
MAX_ITERATIONS = int(os.getenv('MAX_ITERATIONS', '1'))
IMAGEN_MODEL = os.getenv('IMAGEN_MODEL', 'imagen-3.0-generate-002')
GENAI_MODEL = os.getenv('GENAI_MODEL', 'gemini-2.0-flash')