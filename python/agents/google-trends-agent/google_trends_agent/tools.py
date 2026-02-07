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
import json
import os
from dotenv import load_dotenv
from google.cloud import bigquery
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)
GOOGLE_CLOUD_PROJECT = os.getenv('GOOGLE_CLOUD_PROJECT')

def clean_sql_query(text):
    return text.replace('\\n', ' ').replace('\n', ' ').replace('\\', '').replace('```sql', '').replace('```', '').strip()

def execute_bigquery_sql(sql: str) -> str:
    """Executes a BigQuery SQL query and returns the result as a JSON string."""
    print(f'Executing BigQuery SQL query: {sql}')
    cleaned_sql = clean_sql_query(sql)
    print(f'Cleaned SQL query: {cleaned_sql}')
    try:
        client = bigquery.Client(project=GOOGLE_CLOUD_PROJECT)
        query_job = client.query(cleaned_sql)
        results = query_job.result()
        sql_results = [dict(row) for row in results]
        if not sql_results:
            return 'Query returned no results.'
        else:
            return json.dumps(sql_results, default=str).replace('```sql', '').replace('```', '')
    except Exception as e:
        return f'Error executing BigQuery query: {e!s}'