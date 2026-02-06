from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
'Selects a product from BigQuery based on a product name.'
import logging
import os
from google.api_core import exceptions as api_exceptions
from google.cloud import bigquery

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def select_product_from_bq(product_name: str) -> dict:
    """
    Searches for a product in BigQuery by its name within the search_tags
    array.

    Args:
        product_name (str): The name of the product to search for.

    Returns:
        A dictionary representing the matched product row, or None if no match
        is found.
    """
    project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
    dataset_id = 'content_generation'
    table_id = 'media_assets'
    client = bigquery.Client()
    normalized_product_name = product_name.lower().strip()
    query = f"\n        SELECT *\n        FROM `{project_id}.{dataset_id}.{table_id}`\n        WHERE '{normalized_product_name}' IN UNNEST(search_tags)\n    "
    try:
        query_job = client.query(query)
        results = query_job.result()
        for row in results:
            return dict(row)
    except api_exceptions.GoogleAPICallError as e:
        logging.error('An error occurred: %s', e)
        return None
    return None
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    product = select_product_from_bq('power drill')
    if product:
        logging.info('Found product:')
        logging.info(product)
    else:
        logging.info('Product not found.')