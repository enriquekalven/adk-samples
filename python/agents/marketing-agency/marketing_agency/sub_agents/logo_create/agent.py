"""logo_create_agent: for creating logos"""
from google.adk import Agent
from google.adk.tools import ToolContext, load_artifacts
from google.genai import Client, types
from . import prompt
MODEL = 'gemini-2.5-pro'
MODEL_IMAGE = 'imagen-3.0-generate-002'

async def generate_image(img_prompt: str, tool_context: 'ToolContext'):
    """Generates an image based on the prompt."""
    client = Client()
    response = client.models.generate_images(model=MODEL_IMAGE, prompt=img_prompt, config={'number_of_images': 1})
    if not response.generated_images:
        return {'status': 'failed'}
    image_bytes = response.generated_images[0].image.image_bytes
    await tool_context.save_artifact('image.png', types.Part.from_bytes(data=image_bytes, mime_type='image/png'))
    return {'status': 'success', 'detail': 'Image generated successfully and stored in artifacts.', 'filename': 'image.png'}
logo_create_agent = Agent(model=MODEL, name='logo_create_agent', description='An agent that generates images and answers questions about the images.', instruction=prompt.LOGO_CREATE_PROMPT, output_key='logo_create_output', tools=[generate_image, load_artifacts])