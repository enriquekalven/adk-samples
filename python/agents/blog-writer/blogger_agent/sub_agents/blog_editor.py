from google.adk.agents import Agent
from ..agent_utils import suppress_output_callback
from ..config import config
blog_editor = Agent(model=config.critic_model, name='blog_editor', description='Edits a technical blog post based on user feedback.', instruction='\n    You are a professional technical editor. You will be given a blog post and user feedback.\n    Your task is to edit the blog post based on the provided feedback.\n    The final output should be a revised blog post in Markdown format.\n    ', output_key='blog_post', after_agent_callback=suppress_output_callback)