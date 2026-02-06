from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from google.adk.agents.context_cache_config import ContextCacheConfig
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from google.adk.agents.context_cache_config import ContextCacheConfig
from tenacity import retry, wait_exponential, stop_after_attempt
"\nBigQuery integration tools for the cookie delivery system using Google ADK first-party toolset.\nThis file implements BigQuery connectivity using Google's official ADK BigQuery tools.\n"
import logging
import os
import google.auth
from google.adk.tools.bigquery import BigQueryCredentialsConfig, BigQueryToolset
from google.adk.tools.bigquery.config import BigQueryToolConfig, WriteMode
from google.adk.tools.tool_context import ToolContext
PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT', 'your-project-id')
DATASET_ID = 'cookie_delivery'
ORDERS_TABLE = 'orders'

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def get_bigquery_toolset() -> BigQueryToolset:
    """
    Create and configure the ADK BigQuery toolset.
    Uses Application Default Credentials for authentication.
    """
    try:
        tool_config = BigQueryToolConfig(write_mode=WriteMode.ALLOWED)
        application_default_credentials, _ = google.auth.default()
        credentials_config = BigQueryCredentialsConfig(credentials=application_default_credentials)
        bigquery_toolset = BigQueryToolset(credentials_config=credentials_config, bigquery_tool_config=tool_config)
        logging.info('ADK BigQuery toolset initialized successfully')
        return bigquery_toolset
    except Exception as e:
        logging.error(f'Failed to initialize BigQuery toolset: {e}')
        return None

def get_latest_order_from_bigquery(tool_context: ToolContext) -> dict:
    """
    Fetch the latest order with 'order_placed' status from BigQuery using ADK tools.
    This is a wrapper function that uses the ADK execute_sql tool.
    """
    logging.info('Fetching latest order from BigQuery using ADK toolset...')
    try:
        query = f"\n        SELECT *\n        FROM `{PROJECT_ID}.{DATASET_ID}.{ORDERS_TABLE}`\n        WHERE order_status = 'order_placed'\n        ORDER BY created_at DESC\n        LIMIT 1\n        "
        return {'status': 'query_ready', 'query': query, 'instruction': 'Execute this query using the execute_sql tool to get the latest order', 'expected_result': 'order_data'}
    except Exception as e:
        logging.error(f'Error preparing BigQuery query: {e}')
        return {'status': 'error', 'message': f'Query preparation error: {e!s}'}

def update_order_status_in_bigquery(tool_context: ToolContext, order_number: str, new_status: str) -> dict:
    """
    Generate SQL to update order status in BigQuery using ADK tools.
    This function now returns SQL for execution by the ADK toolset instead of executing directly.
    """
    logging.info(f'Preparing order status update for {order_number} to {new_status}...')
    try:
        query = f"\n        UPDATE `{PROJECT_ID}.{DATASET_ID}.{ORDERS_TABLE}`\n        SET order_status = '{new_status}', \n            updated_at = CURRENT_TIMESTAMP()\n        WHERE order_number = '{order_number}'\n        "
        return {'status': 'query_ready', 'query': query, 'instruction': f'Execute this query to update order {order_number} status to {new_status}', 'order_number': order_number, 'new_status': new_status}
    except Exception as e:
        logging.error(f'Error preparing update query: {e}')
        return {'status': 'error', 'message': f'Update query error: {e!s}'}

def get_order_analytics_query(tool_context: ToolContext, days: int=30) -> dict:
    """
    Generate analytics query for BigQuery using ADK tools.
    """
    logging.info(f'Preparing analytics query for last {days} days...')
    try:
        query = f'\n        SELECT \n            order_status,\n            COUNT(*) as order_count,\n            AVG(total_amount) as avg_order_value,\n            SUM(total_amount) as total_revenue\n        FROM `{PROJECT_ID}.{DATASET_ID}.{ORDERS_TABLE}`\n        WHERE DATE(created_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)\n        GROUP BY order_status\n        ORDER BY order_count DESC\n        '
        return {'status': 'query_ready', 'query': query, 'instruction': f'Execute this query to get order analytics for the last {days} days', 'days': days}
    except Exception as e:
        logging.error(f'Error preparing analytics query: {e}')
        return {'status': 'error', 'message': f'Analytics query error: {e!s}'}

def get_dataset_setup_queries() -> list[dict]:
    """
    Generate queries to set up the BigQuery dataset and tables.
    """
    queries = []
    dataset_query = f"\n    CREATE SCHEMA IF NOT EXISTS `{PROJECT_ID}.{DATASET_ID}`\n    OPTIONS (\n        description = 'Cookie delivery order management dataset',\n        location = 'US'\n    )\n    "
    queries.append({'description': 'Create cookie_delivery dataset', 'query': dataset_query})
    table_query = f'\n    CREATE TABLE IF NOT EXISTS `{PROJECT_ID}.{DATASET_ID}.{ORDERS_TABLE}` (\n        order_id STRING NOT NULL,\n        order_number STRING NOT NULL,\n        customer_email STRING NOT NULL,\n        customer_name STRING NOT NULL,\n        customer_phone STRING,\n        order_items ARRAY<STRUCT<\n            item_name STRING,\n            quantity INT64,\n            unit_price FLOAT64\n        >>,\n        delivery_address STRUCT<\n            street STRING,\n            city STRING,\n            state STRING,\n            zip_code STRING,\n            country STRING\n        >,\n        delivery_location STRING,\n        delivery_request_date DATE,\n        delivery_time_preference STRING,\n        order_status STRING NOT NULL,\n        total_amount FLOAT64,\n        order_date TIMESTAMP,\n        special_instructions STRING,\n        created_at TIMESTAMP,\n        updated_at TIMESTAMP\n    )\n    CLUSTER BY order_status\n    '
    queries.append({'description': 'Create orders table with proper schema', 'query': table_query})
    sample_orders = [{'order_id': 'ORD12345', 'order_number': 'ORD12345', 'customer_email': 'john.doe@example.com', 'customer_name': 'John Doe', 'customer_phone': '+1-555-0123', 'delivery_location': '123 Main St, Anytown, CA 12345, USA', 'delivery_request_date': '2025-09-16', 'delivery_time_preference': 'morning', 'order_status': 'order_placed', 'total_amount': 63.5, 'special_instructions': 'Please ring doorbell twice'}, {'order_id': 'ORD12346', 'order_number': 'ORD12346', 'customer_email': 'jane.smith@example.com', 'customer_name': 'Jane Smith', 'customer_phone': '+1-555-0124', 'delivery_location': '456 Oak Ave, Springfield, CA 67890, USA', 'delivery_request_date': '2025-09-17', 'delivery_time_preference': 'afternoon', 'order_status': 'order_placed', 'total_amount': 99.0, 'special_instructions': 'Leave at front door'}]
    for order in sample_orders:
        insert_query = f"\n        INSERT INTO `{PROJECT_ID}.{DATASET_ID}.{ORDERS_TABLE}` \n        (order_id, order_number, customer_email, customer_name, customer_phone,\n         order_items, delivery_address, delivery_location, delivery_request_date,\n         delivery_time_preference, order_status, total_amount, order_date,\n         special_instructions, created_at, updated_at)\n        VALUES (\n            '{order['order_id']}',\n            '{order['order_number']}', \n            '{order['customer_email']}',\n            '{order['customer_name']}',\n            '{order['customer_phone']}',\n            [STRUCT('Chocolate Chip' as item_name, 12 as quantity, 2.50 as unit_price),\n             STRUCT('Oatmeal Raisin' as item_name, 6 as quantity, 2.75 as unit_price)],\n            STRUCT(\n                '123 Main St' as street,\n                'Anytown' as city, \n                'CA' as state,\n                '12345' as zip_code,\n                'USA' as country\n            ),\n            '{order['delivery_location']}',\n            DATE('{order['delivery_request_date']}'),\n            '{order['delivery_time_preference']}',\n            '{order['order_status']}',\n            {order['total_amount']},\n            CURRENT_TIMESTAMP(),\n            '{order['special_instructions']}',\n            CURRENT_TIMESTAMP(),\n            CURRENT_TIMESTAMP()\n        )\n        "
        queries.append({'description': f"Insert sample order {order['order_number']}", 'query': insert_query})
    return queries