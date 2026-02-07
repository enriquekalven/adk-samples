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

from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
import os
from google.adk.agents import Agent
from google.adk.tools import MCPToolset
from google.adk.tools.mcp_tool import StdioConnectionParams
from mcp import StdioServerParameters
root_agent = Agent(name='antom_payment_agent', model='gemini-2.0-flash', description='Agent creates payment links for merchants, queries payment result details。', instruction='You are an Antom payment agent who can help users create payment links and query payment result details.Regarding RequestId, you generate it randomlyAnd you can describe the description of the user creating the order in one sentencewhen refund get the order details and paymentId based on the paymentRequest ID used when creating the payment method by the payment agent. If the merchant specifies a refund amount, a full refund will be made in the order currency by default.', tools=[MCPToolset(connection_params=StdioConnectionParams(server_params=StdioServerParameters(command='uvx', args=['ant-intl-antom-mcp'], env={'GATEWAY_URL': os.getenv('GATEWAY_URL'), 'CLIENT_ID': os.getenv('CLIENT_ID'), 'MERCHANT_PRIVATE_KEY': os.getenv('MERCHANT_PRIVATE_KEY'), 'ALIPAY_PUBLIC_KEY': os.getenv('ALIPAY_PUBLIC_KEY'), 'PAYMENT_REDIRECT_URL': os.getenv('PAYMENT_REDIRECT_URL'), 'PAYMENT_NOTIFY_URL': os.getenv('PAYMENT_NOTIFY_URL')})))])