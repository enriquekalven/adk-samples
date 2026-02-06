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
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
'This module provides a set of tools for interacting with Google BigQuery.\n\nIt includes functionalities for checking dataset and table existence, retrieving\ntable schemas and data previews, validating dataset and table names, querying\ninformation schema, finding relevant datasets, and validating data within tables\nbased on user-defined rules.\n'
import json
from typing import Any
from google.cloud import bigquery
from ..config import config

def get_bigquery_client() -> bigquery.Client:
    """Get a configured BigQuery client."""
    return bigquery.Client(project=config.project_id)

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def bigquery_job_details_tool(job_id: str) -> dict[str, Any]:
    """Retrieve details of a BigQuery job.

    Args:
        job_id (str): The ID of the BigQuery job.

    Returns:
        Dict[str, Any]: Job details including query and error information.
    """
    client = get_bigquery_client()
    try:
        job = client.get_job(job_id)
        query = job.query if isinstance(job, bigquery.QueryJob) else 'N/A'
        errors = job.error_result
        return {'query': query, 'status': job.state, 'error': errors['message'] if errors else None, 'created': job.created.isoformat(), 'started': job.started.isoformat() if job.started else None, 'ended': job.ended.isoformat() if job.ended else None}
    except Exception as e:
        return {'error': f'Error getting job details: {e}'}

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def get_udf_sp_tool(dataset_id: str, routine_type: str | None=None) -> str:
    """Retrieve UDFs and Stored Procedures from a BigQuery dataset.

    Args:
        dataset_id (str): The dataset ID to search.
        routine_type (Optional[str]): Filter by routine type ('FUNCTION' or
          'PROCEDURE').

    Returns:
        str: JSON string containing routine information.
    """
    client = get_bigquery_client()
    query = f"""\n        SELECT \n            routine_name,\n            routine_type,\n            routine_body,\n            specific_name,\n            ddl,\n            routine_definition,\n            created,\n            last_modified\n        FROM `{config.project_id}.{dataset_id}.INFORMATION_SCHEMA.ROUTINES`\n        {(f"WHERE routine_type = '{routine_type}'" if routine_type else '')}\n        ORDER BY routine_type, routine_name\n    """
    try:
        query_job = client.query(query)
        results = query_job.result()
        routine_info_list = [dict(row.items()) for row in results]
        if not routine_info_list:
            return json.dumps({'message': f"No {('UDFs' if routine_type == 'FUNCTION' else 'Stored Procedures' if routine_type == 'PROCEDURE' else 'routines')} found in dataset '{dataset_id}'."}, indent=2)
        return json.dumps(routine_info_list, indent=2, default=str)
    except Exception as e:
        return json.dumps({'error': f"Error retrieving routines from dataset '{dataset_id}': {e}"}, indent=2)

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def validate_table_data(dataset_id: str, table_id: str, rules: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate data in a BigQuery table against specified rules.

    Args:
        dataset_id (str): The dataset ID.
        table_id (str): The table ID.
        rules (List[Dict[str, Any]]): List of validation rules.

    Returns:
        Dict[str, Any]: Validation results.
    """
    client = get_bigquery_client()
    validation_results = []
    for rule in rules:
        try:
            column = rule['column']
            rule_type = rule['type']
            value = rule.get('value')
            if rule_type == 'not_null':
                query = f'\n                    SELECT COUNT(*) as null_count\n                    FROM `{config.project_id}.{dataset_id}.{table_id}`\n                    WHERE {column} IS NULL\n                '
            elif rule_type == 'unique':
                query = f'\n                    SELECT {column}, COUNT(*) as count\n                    FROM `{config.project_id}.{dataset_id}.{table_id}`\n                    GROUP BY {column}\n                    HAVING COUNT(*) > 1\n                '
            elif rule_type == 'value':
                query = f'\n                    SELECT COUNT(*) as invalid_count\n                    FROM `{config.project_id}.{dataset_id}.{table_id}`\n                    WHERE {column} != {value}\n                '
            else:
                validation_results.append({'rule': rule, 'status': 'error', 'message': f'Unknown rule type: {rule_type}'})
                continue
            query_job = client.query(query)
            results = query_job.result()
            row = next(iter(results))
            validation_results.append({'rule': rule, 'status': 'pass' if row[0] == 0 else 'fail', 'details': dict(row.items())})
        except Exception as e:
            validation_results.append({'rule': rule, 'status': 'error', 'message': str(e)})
    return {'dataset': dataset_id, 'table': table_id, 'validations': validation_results}

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def sample_table_data_tool(dataset_id: str, table_id: str, sample_size: int=10, random_seed: int | None=None) -> str:
    """Sample data from a BigQuery table using RAND() function.

    Args:
        dataset_id (str): The dataset ID.
        table_id (str): The table ID.
        sample_size (int): Number of rows to sample. Defaults to 10.
        random_seed (Optional[int]): Seed for random sampling. If provided,
          ensures reproducible results.

    Returns:
        str: JSON string containing sampled data.
    """
    try:
        client = get_bigquery_client()
        seed_clause = f'SET @seed = {random_seed};' if random_seed is not None else ''
        query = f"\n            {seed_clause}\n            SELECT *\n            FROM `{config.project_id}.{dataset_id}.{table_id}`\n            ORDER BY {('RAND(@seed)' if random_seed is not None else 'RAND()')}\n            LIMIT {sample_size}\n        "
        query_job = client.query(query)
        results = query_job.result()
        sample_data = [dict(row.items()) for row in results]
        return json.dumps({'status': 'success', 'dataset': dataset_id, 'table': table_id, 'sample_size': sample_size, 'random_seed': random_seed, 'data': sample_data}, indent=2, default=str)
    except Exception as e:
        return json.dumps({'status': 'error', 'error': str(e)}, indent=2)