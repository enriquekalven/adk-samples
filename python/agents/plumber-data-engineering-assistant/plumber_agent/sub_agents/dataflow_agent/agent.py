"""Dataflow agent."""
from google.adk.agents import Agent
from .constants import MODEL
from .prompts import AGENT_INSTRUCTION
from .tools.dataflow_management_utils import cancel_dataflow_job, get_dataflow_job_details, list_dataflow_jobs
from .tools.dataflow_template_tools import get_dataflow_template, submit_dataflow_template
from .tools.pipeline_utils import create_pipeline_from_scratch, generate_beam_transformations_from_sttm, review_dataflow_code
root_agent = Agent(name='dataflow_agent', model=MODEL, description='A powerful agent that can create, deploy, and manage Google Cloud Dataflow jobs, and find, customize, and build Dataflow templates.', instruction=AGENT_INSTRUCTION, tools=[create_pipeline_from_scratch, generate_beam_transformations_from_sttm, review_dataflow_code, list_dataflow_jobs, get_dataflow_job_details, cancel_dataflow_job, get_dataflow_template, submit_dataflow_template])