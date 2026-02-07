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
'Tools for managing and orchestrating Google Cloud Dataproc templates.'
import json
import logging
import os
import shutil
import subprocess
import uuid
import vertexai
from dotenv import load_dotenv
from google.cloud import storage
from vertexai.generative_models import GenerativeModel, Image
from ..constants import JAVA_TEMPLATE_START_SCRIPT_BIN_PATH, LANGUAGE_OPTIONS, MODEL, PYTHON_TEMPLATE_START_SCRIPT_BIN_PATH, TEMP_DIR_PATH, TEMPLATE_REPO_PATH
from ..prompts import STTM_PARSING_INSTRUCTIONS
from ..utils import find_files, get_dataproc_template_mapping, get_dataproc_template_repo, update_dataproc_template, validate_input_params
logger = logging.getLogger('plumber-agent')
load_dotenv()
vertexai.init(project=os.getenv('GOOGLE_CLOUD_PROJECT'), location=os.getenv('GOOGLE_CLOUD_LOCATION'))

def get_transformation_sql(gcs_url: str) -> dict[str, str]:
    """
    Generates SQL transformation code from a file stored in Google Cloud Storage (GCS),
    using a generative AI model. Supports CSV and image file formats.

    Parameters:
        gcs_url (str): The GCS URL pointing to the input file
            (e.g., "gs://bucket_name/path/to/file.csv").

    Returns:
        dict: A dictionary containing:
            - "status" (str): A message indicating success or failure reason.
            - "sql" (str): The generated SQL transformation query (empty on failure).

    Exceptions:
        - Returns a failure status with the error message if any unhandled exception occurs.
    """
    try:
        if not gcs_url.startswith('gs://'):
            return {'status': 'failure - Invalid GCS Path', 'sql': ''}
        bucket_name, file_path = gcs_url[5:].split('/', 1)
        file_type = file_path.split('/')[-1].split('.')[1]
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_path)
        model = GenerativeModel(MODEL)
        if not blob.exists():
            return {'status': 'failure - Object not available at input path', 'sql': ''}
        file_bytes = blob.download_as_bytes()
        if file_type == 'csv':
            file_content = file_bytes.decode('utf-8')
            response = model.generate_content([STTM_PARSING_INSTRUCTIONS, file_content])
        else:
            image = Image.from_bytes(file_bytes)
            response = model.generate_content([STTM_PARSING_INSTRUCTIONS, image])
        output_sql = response.text.replace('```sql', '').replace('```', '')
        return {'status': 'success', 'sql': output_sql}
    except Exception as err:
        logger.error('An error occurred in get_transformation_sql: %s', err, exc_info=True)
        return {'status': f'failure - {err!s}', 'sql': ''}

def get_dataproc_template(user_prompt: str, language: LANGUAGE_OPTIONS) -> dict[str, str]:
    """
    Retrieves the most relevant Dataproc template based on the user's prompt
    and selected programming language (Python or Java).

    This function clones or accesses a local copy of the Dataproc templates GitHub repository,
    searches for README files related to available templates, and uses a matching
    mechanism to find the template that best fits the user prompt.

    Parameters:
        user_prompt (str): A natural language description of the desired data processing task.
        language (LANGUAGE_OPTIONS): The programming language to filter templates by
            (e.g., "Python" or "Java").

    Returns:
        dict:
            - If successful: A dictionary with information about the matched template
              (e.g., name, description, path).
            - If the repo clone fails or no match is found: A dictionary indicating failure status.
    """
    try:
        status = get_dataproc_template_repo()
        if status.get('repo_path'):
            readme_files = []
            if language == 'Python':
                readme_files = find_files(directory=f"{status['repo_path']}/python/dataproc_templates/", regex='README.md')
            elif language == 'Java':
                readme_files = find_files(directory=f"{status['repo_path']}/java/src/main/java/com/google/cloud/dataproc/templates", regex='README.md')
            matched_template = get_dataproc_template_mapping(readme_files, user_prompt, language)
            return matched_template
        return status
    except Exception as err:
        logger.error('An error occurred in get_dataproc_template: %s', err, exc_info=True)
        return {'status': 'failed', 'error': str(err)}

def run_dataproc_template(language: str, template_name: str, input_params: str, template_params: str, template_path: str, GCP_PROJECT: str, REGION: str, GCS_STAGING_LOCATION: str, GCS_DEPS_BUCKET: str, JARS: str='', SUBNET: str='', SPARK_PROPERTIES: str='', TRANSFORMATION_SQL: str='') -> dict[str, str]:
    """
    Submits a Dataproc job using a specified template with user-provided parameters
    and optional transformation logic.

    This function handles input validation, environment setup, and execution of a Dataproc
    template (in Python or Java), and optionally modifies the template to include transformation
    SQL logic. It returns the result of the job execution.

    Args:
        language (str): Programming language of the template ("Python" or "Java").
        template_name (str): Name of the Dataproc template to run.
        input_params (str): JSON string of input parameters provided by the user.
        template_params (str): JSON string of expected parameters defined in the template.
        template_path (str): Path to the template script or entry point.
        GCP_PROJECT (str): Google Cloud project ID.
        REGION (str): Region where the Dataproc cluster should run.
        GCS_STAGING_LOCATION (str): GCS path for staging files.
        JARS (str, optional): Comma-separated list of JAR files for Java templates.
        SUBNET (str, optional): Subnet to use for the job.
        SPARK_PROPERTIES (str, optional): Additional Spark properties to configure.
        TRANSFORMATION_SQL (str, optional): SQL string to inject into the template
            before execution (used for dynamic transformation logic).

    Returns:
        dict: A dictionary containing:
            - "status" (str): "success" or "failed".
            - "comment" (str): Job output or error message.
            - "run_cmd" (str, optional): The full command executed (on error).
            - "environments" (str, optional): Environment variables used (on error).

    Raises:
        subprocess.CalledProcessError: If the template execution command fails.
        Exception: For any unexpected errors during setup or execution.
    """
    try:
        temp_template_repo_path = ''
        run_id = str(uuid.uuid4())
        if language.upper() == 'JAVA':
            template_bin_path = JAVA_TEMPLATE_START_SCRIPT_BIN_PATH
        else:
            template_bin_path = PYTHON_TEMPLATE_START_SCRIPT_BIN_PATH
        input_params_dict = json.loads(input_params)
        template_params_dict = json.loads(template_params)
        param_validation_result = validate_input_params(template_params_dict, input_params_dict)
        if param_validation_result['validation_result'] != 'success':
            return {'status': 'failed', 'comment': f"Job could not be submitted due to error while parameters validations: {param_validation_result['comment']}"}
        if TRANSFORMATION_SQL:
            template_file_name = template_path.split('/')[-1]
            template_dir = os.path.dirname(template_path)
            temp_template_repo_path = update_dataproc_template(run_id, template_file_name, template_dir, TRANSFORMATION_SQL)
            template_bin_path = template_bin_path.replace(TEMPLATE_REPO_PATH, temp_template_repo_path)
        my_env = os.environ.copy()
        my_env['GCP_PROJECT'] = GCP_PROJECT
        my_env['REGION'] = REGION
        my_env['GCS_STAGING_LOCATION'] = GCS_STAGING_LOCATION
        my_env['GCS_DEPS_BUCKET'] = GCS_DEPS_BUCKET
        if JARS:
            my_env['JARS'] = JARS
        if SUBNET:
            my_env['SUBNET'] = SUBNET
        if SPARK_PROPERTIES:
            my_env['SPARK_PROPERTIES'] = SPARK_PROPERTIES
        if os.getenv('PLUMBER_TARGET_SERVICE_ACCOUNT_ID'):
            my_env['OPT_SERVICE_ACCOUNT_NAME'] = f" --impersonate-service-account={os.getenv('PLUMBER_TARGET_SERVICE_ACCOUNT_ID')} --labels=submitted_from=plumber"
        else:
            my_env['OPT_SERVICE_ACCOUNT_NAME'] = '--labels=submitted_from=plumber'
        run_cmd = ['./bin/start.sh', '--', f'--template={template_name}']
        if language.upper() == 'PYTHON':
            for param, value in input_params_dict.items():
                run_cmd.append(f'--{param}={value}')
        elif language.upper() == 'JAVA':
            for param, value in input_params_dict.items():
                run_cmd.extend(['--templateProperty', f'{param}={value}'])
        output = subprocess.run(run_cmd, capture_output=True, text=True, check=True, env=my_env, cwd=os.path.abspath(f'./{template_bin_path}'))
        if temp_template_repo_path:
            shutil.rmtree(f'./{TEMP_DIR_PATH}/{run_id}')
        return {'status': 'success', 'comment': f'Job Run Completed Successfully - {output.stdout}'}
    except subprocess.CalledProcessError as cmd_err:
        if temp_template_repo_path:
            shutil.rmtree(f'./{TEMP_DIR_PATH}/{run_id}')
        return {'status': 'failed', 'comment': f'Job Failed - 1 {cmd_err.stderr!s}', 'run_cmd': run_cmd}
    except Exception as err:
        logger.error('An error occurred in get_dataproc_template: %s', err, exc_info=True)
        if temp_template_repo_path:
            shutil.rmtree(f'./{TEMP_DIR_PATH}/{run_id}')
        return {'status': 'failed', 'comment': f'Job Failed - 2 {err!s}', 'run_cmd': run_cmd}