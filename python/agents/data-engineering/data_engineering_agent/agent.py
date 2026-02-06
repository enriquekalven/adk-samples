from google.adk.agents.context_cache_config import ContextCacheConfig
from tenacity import retry, wait_exponential, stop_after_attempt
from google.adk.agents.context_cache_config import ContextCacheConfig
from tenacity import retry, wait_exponential, stop_after_attempt
import google.auth
from google.adk import Agent
from google.adk.tools.bigquery import BigQueryCredentialsConfig, BigQueryToolset
from google.adk.tools.bigquery.config import BigQueryToolConfig, WriteMode
from .config import config
from .tools.bigquery_tools import get_udf_sp_tool, sample_table_data_tool
from .tools.dataform_tools import compile_dataform, delete_file_from_dataform, get_dataform_execution_logs, get_dataform_repo_link, read_file_from_dataform, search_files_in_dataform, write_file_to_dataform
from .tools.gcs_tools import list_bucket_files_tool, read_gcs_file_tool, validate_bucket_exists_tool, validate_file_exists_tool
tool_config = BigQueryToolConfig(write_mode=WriteMode.BLOCKED)
application_default_credentials, _ = google.auth.default()
credentials_config = BigQueryCredentialsConfig(credentials=application_default_credentials)
bigquery_toolset = BigQueryToolset(credentials_config=credentials_config, bigquery_tool_config=tool_config)
root_agent = Agent(model=config.root_agent_model, name='data_engineering_agent', instruction=f'\n      You are a BigQuery and Dataform ELT expert.\n\n      You need to generate Dataform pipeline SQLX code to perform ELT operations for the user-requested tasks.\n\n      Plan the user task by breaking it into smaller steps.\n\n      - Get an overview of the Dataform pipeline DAG from the compilation result.\n      - If needed, sample the tables or resolved SQLX actions from the pipeline DAG.\n      - Per user request, make changes to the Dataform files.\n      - Compile the pipeline and fix any errors.\n"\n      - Validate the resolved queries for the changed nodes and fix any errors.\n      - Repeat these steps iteratively until the user task is completed.\n\n      Configuration:\n      Default Project ID is {config.project_id} use this project ID for all BigQuery queries unless otherwise specified.\n\n      Dataform\n        Source files\n        BigQuery Source Tables**: For each BigQuery source table, always add/generate a declarations file. Use the following format for declarations in SQLX files:\n        config {{\n          type: "declaration",\n          database: "PROJECT_ID",\n          schema: "DATASET_ID",\n          name: "TABLE_NAME",\n        }}\n\n      Always verify your changes and ensure they meet the requirements.\n      Make reasonable assumptions and do not ask so many questions.\n      Compile the pipeline and fix any issues.\n      Do not run destructive SQL operations (i.e: drop)\n    ', tools=[write_file_to_dataform, compile_dataform, get_dataform_execution_logs, search_files_in_dataform, read_file_from_dataform, delete_file_from_dataform, get_dataform_repo_link, get_udf_sp_tool, bigquery_toolset, sample_table_data_tool, validate_bucket_exists_tool, validate_file_exists_tool, list_bucket_files_tool, read_gcs_file_tool], context_cache_config=ContextCacheConfig(min_tokens=2048, ttl_seconds=600))