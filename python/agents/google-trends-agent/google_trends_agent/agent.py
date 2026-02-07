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

import os
from dotenv import load_dotenv
from google.adk.agents import LlmAgent, SequentialAgent
from google_trends_agent.prompt import load_agent_instructions
from google_trends_agent.tools import execute_bigquery_sql
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)
MODEL_AGENT = os.getenv('MODEL_AGENT', 'gemini-2.5-pro')
MODEL_TOOL = os.getenv('MODEL_TOOL', 'gemini-2.5-flash')
full_instruction = load_agent_instructions()
trends_query_generator_agent = LlmAgent(name='TrendsQueryGeneratorAgent', model=MODEL_AGENT, instruction=full_instruction, description="Generates a BigQuery SQL query based on the user's question about Google Trends.", output_key='generated_sql')
trends_query_executor_agent = LlmAgent(name='TrendsQueryExecutorAgent', model=MODEL_TOOL, instruction='You are a SQL execution agent.\nYour task is to execute the BigQuery SQL query provided in the `{generated_sql}` placeholder.\nUse the execute_bigquery_sql tool to run the query.\nThe query is already written; do not modify it. Simply pass it to the tool.\nRead the query results and give insights to the user.\n', description='Executes the generated SQL query using the execute_bigquery_sql tool.', tools=[execute_bigquery_sql])
print(trends_query_executor_agent.instruction)
root_agent = SequentialAgent(name='GoogleTrendsAgent', sub_agents=[trends_query_generator_agent, trends_query_executor_agent], description='A two-step pipeline that first generates a SQL query for Google Trends and then executes it.\n    Format the output as user friendly markdown format. Separete the SQL query and the interpretation of the results with a horizontal line.')