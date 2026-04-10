# Copyright 2025 Google LLC. This software is provided as-is, without warranty or representation.
"""
Modernized Deployment script for Economic Research Agent using Vertex AI Agent Engine (ADK 2.1+).
"""

import logging
import os

import cloudpickle
import vertexai
from vertexai import agent_engines
from vertexai.preview.reasoning_engines import AdkApp

import economic_research
from economic_research.agent import ERAAgent

logging.getLogger("google.cloud.aiplatform").setLevel(logging.DEBUG)
cloudpickle.register_pickle_by_value(economic_research)


def deploy_era_to_vertex(project_id: str, location: str = "us-central1"):
    print(
        f"🚀 Initializing Modern Agent Engine Deployment for economic-research in {location}..."
    )

    # AdkApp requires a staging_bucket to persist dependencies and serialized objects
    # Defaulting to project_id-agent-engine-v16 which we saw was valid for project-maui
    staging_bucket = os.getenv(
        "GOOGLE_CLOUD_STORAGE_BUCKET", f"gs://{project_id}-agent-engine-v16"
    )
    print(f"🪣 Using staging bucket: {staging_bucket}")

    vertexai.init(
        project=project_id, location=location, staging_bucket=staging_bucket
    )

    # Calculate absolute path for extra_packages
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    agent_package_path = project_root

    print(f"📦 Packaging from: {agent_package_path}")

    # Read requirements from requirements.txt
    requirements_path = os.path.join(project_root, "requirements.txt")
    with open(requirements_path) as f:
        requirements = [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#")
        ]

    era_instance = ERAAgent()
    root_agent = era_instance.get_app().root_agent

    adk_app = AdkApp(
        agent=root_agent,
        enable_tracing=False,
    )

    # Use the new agent_engines API
    remote_agent = agent_engines.create(
        adk_app,
        requirements=requirements,
        extra_packages=[os.path.join(project_root, "economic_research")],
        display_name="adk-economic-agent",
    )

    print("✅ Modern Deployment Successful!")
    print(f"Agent Engine ID: {remote_agent.resource_name}")
    return remote_agent.resource_name


if __name__ == "__main__":
    import google.auth

    try:
        _, project = google.auth.default()
        active_project = project or os.getenv(
            "GOOGLE_CLOUD_PROJECT", "project-maui"
        )
        deploy_era_to_vertex(project_id=active_project)
    except Exception as e:
        print(f"❌ Modern Deployment Failed: {e}")
