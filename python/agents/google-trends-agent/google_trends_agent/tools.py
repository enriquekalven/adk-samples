from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
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

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
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