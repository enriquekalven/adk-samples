# Copyright 2026 Google LLC
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

"""Wrapper script to deploy the Economic Research Agent with API keys loaded from .env."""

import subprocess

from dotenv import dotenv_values


def deploy():
    # Load all variables from .env
    env_vars = dotenv_values(".env")

    # Select keys to deploy
    keys_to_deploy = [
        "BEA_API_KEY",
        "FRED_API_KEY",
        "CENSUS_API_KEY",
        "BLS_API_KEY",
        "HUD_API_KEY",
        "FEC_API_KEY",
        "EIA_API_KEY",
        "NEWS_API_KEY",
        "SERPER_API_KEY",
    ]

    deploy_env_list = []
    for k in keys_to_deploy:
        val = env_vars.get(k)
        if val:
            # Clean quotes if any
            val = val.strip().replace('"', "").replace("'", "")
            deploy_env_list.append(f"{k}={val}")

    env_str = ",".join(deploy_env_list)

    # Construct deploy command
    cmd = [
        "uv",
        "run",
        "agents-cli",
        "deploy",
        "--no-confirm-project",
        "--update-env-vars",
        env_str,
    ]

    print("🚀 Starting deployment to Agent Runtime with local API keys...")
    print(f"Command: {' '.join(cmd)[:200]}... [truncated keys]")

    result = subprocess.run(cmd, capture_output=False, check=False)
    if result.returncode == 0:
        print(
            "✅ Deployed and configured with environment variables successfully!"
        )
    else:
        print(f"❌ Deployment failed with exit code: {result.returncode}")


if __name__ == "__main__":
    deploy()
