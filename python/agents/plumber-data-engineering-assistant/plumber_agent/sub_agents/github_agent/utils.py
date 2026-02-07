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
'Utils.py file'
import getpass
import os
from dotenv import load_dotenv
load_dotenv()
USER_AGENT = 'GitHub-Downloader-ADK/2.0'

def _create_github_headers(token: str='') -> dict[str, str]:
    """
    Creates a standard set of headers for GitHub API requests.

    Includes the 'Accept' and 'User-Agent' headers. If a token is provided,
    it also adds the 'Authorization' header for authenticated requests.

    Args:
        token (str, optional): A GitHub Personal Access Token. Defaults to "".

    Returns:
        Dict[str, str]: A dictionary containing the HTTP headers.
    """
    headers = {'Accept': 'application/vnd.github.v3+json', 'User-Agent': USER_AGENT}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    return headers

def _get_auth_token(token: str='') -> str:
    """
    Retrieves a GitHub authentication token from various sources.

    The function prioritizes sources in the following order:
    1. A token passed directly to the function.
    2. The 'GITHUB_TOKEN' environment variable.
    3. A secure prompt asking the user to enter the token.

    Args:
        token (str, optional): A GitHub token provided directly. Defaults to "".

    Returns:
        str: The retrieved and cleaned (stripped of whitespace) GitHub token.
    """
    token = token or os.getenv('GITHUB_TOKEN')
    if not token or not token.strip():
        token = getpass.getpass('Enter your GitHub Personal Access Token: ')
    return token.strip()

def _parse_repo_path(repository: str) -> tuple[str | None, str | None]:
    """
    Parses a repository string to extract the owner and repository name.

    Handles both full GitHub URLs (http/https) and the shorthand 'owner/repo' format.

    Args:
        repository (str): The repository identifier string (e.g., 'https://github.com/owner/repo'
                          or 'owner/repo').

    Returns:
        tuple[str | None, str | None]: A tuple containing the owner and the repository name.
                                       Returns (None, None) if the format is invalid.
    """
    if repository.startswith(('http://', 'https://')):
        repo_path = repository.split('github.com/')[-1].rstrip('.git')
    else:
        repo_path = repository
    if '/' not in repo_path:
        return (None, None)
    return repo_path.split('/', 1)