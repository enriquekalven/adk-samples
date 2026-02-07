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
'\nThis module provides functionality to run dbt projects locally using\nsubprocess calls to the dbt CLI.\n'
import logging
import subprocess
logger = logging.getLogger('plumber-agent')

def run_dbt_project(dbt_project_path: str) -> dict[str, str | int | None]:
    """
    Runs dbt commands to debug and execute a dbt project located at the specified path.

    This function performs the following steps:
      - Runs `dbt debug` to check the project and profile configuration.
      - Runs `dbt run` to execute the dbt models.
      - Captures and returns the result, including status, return code, and output logs.

    Args:
        dbt_project_path (str): Local filesystem path to the root directory of
          the dbt project. This directory should contain both the
          `dbt_project.yml` and profiles.

    Returns:
        dict: A dictionary containing:
            - "status" (str): "success" if `dbt run` completes successfully,
                              "error" if a CalledProcessError is raised,
                              or "failure" for any other exception.
            - "return_code" (int or None): The return code of the `dbt run` process,
                                          or None if an unexpected error occurred.
            - "output" (str): The standard output from `dbt run` if successful,
                              or standard error if an error occurred,
                              or the exception message on failure.
    """
    try:
        subprocess.run(['dbt', 'debug', '--project-dir', dbt_project_path, '--profiles-dir', dbt_project_path], capture_output=True, text=True, check=True)
        dbt_run_status = subprocess.run(['dbt', 'run', '--project-dir', dbt_project_path, '--profiles-dir', dbt_project_path], capture_output=True, text=True, check=True)
        return {'status': 'success', 'return_code': dbt_run_status.returncode, 'output': dbt_run_status.stdout}
    except subprocess.CalledProcessError as cmd_err:
        logger.error('An error occurred: %s', cmd_err, exc_info=True)
        return {'status': 'error', 'return_code': cmd_err.returncode, 'output': cmd_err.stderr}
    except Exception as err:
        logger.error('An error occurred: %s', err, exc_info=True)
        return {'status': 'failure', 'return_code': None, 'output': str(err)}