from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
import os
from datetime import datetime
from google import genai
from google.adk.tools import ToolContext
from google.cloud import storage
from google.genai import types
from .... import config
client = genai.Client(vertexai=True, project=os.environ.get('GOOGLE_CLOUD_PROJECT'), location='global')

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
async def generate_images(imagen_prompt: str, tool_context: ToolContext):
    try:
        response = client.models.generate_images(model=config.IMAGEN_MODEL, prompt=imagen_prompt, config=types.GenerateImagesConfig(number_of_images=1, aspect_ratio='9:16', safety_filter_level='block_low_and_above', person_generation='allow_adult'))
        if response.generated_images is not None:
            for generated_image in response.generated_images:
                image_bytes = generated_image.image.image_bytes
                counter = str(tool_context.state.get('loop_iteration', 0))
                artifact_name = f'generated_image_{counter}.png'
                if config.GCS_BUCKET_NAME:
                    save_to_gcs(tool_context, image_bytes, artifact_name, counter)
                report_artifact = types.Part.from_bytes(data=image_bytes, mime_type='image/png')
                await tool_context.save_artifact(artifact_name, report_artifact)
                print(f'Image also saved as ADK artifact: {artifact_name}')
                return {'status': 'success', 'message': f'Image generated .  ADK artifact: {artifact_name}.', 'artifact_name': artifact_name}
        else:
            error_details = str(response)
            print(f'No images generated. Response: {error_details}')
            return {'status': 'error', 'message': f'No images generated. Response: {error_details}'}
    except Exception as e:
        return {'status': 'error', 'message': f'No images generated. {e}'}

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def save_to_gcs(tool_context: ToolContext, image_bytes, filename: str, counter: str):
    storage_client = storage.Client()
    bucket_name = config.GCS_BUCKET_NAME
    unique_id = tool_context.state.get('unique_id', '')
    current_date_str = datetime.utcnow().strftime('%Y-%m-%d')
    unique_filename = filename
    gcs_blob_name = f'{current_date_str}/{unique_id}/{unique_filename}'
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(gcs_blob_name)
    try:
        blob.upload_from_string(image_bytes, content_type='image/png')
        gcs_uri = f'gs://{bucket_name}/{gcs_blob_name}'
        tool_context.state['generated_image_gcs_uri_' + counter] = gcs_uri
    except Exception as e_gcs:
        return {'status': 'error', 'message': f'Image generated but failed to upload to GCS: {e_gcs}'}