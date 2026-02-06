from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from google.adk.tools import ToolContext

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
async def get_image(tool_context: ToolContext):
    try:
        artifact_name = f"generated_image_{tool_context.state.get('loop_iteration', 0)}.png"
        await tool_context.load_artifact(artifact_name)
        return {'status': 'success', 'message': f'Image artifact {artifact_name} successfully loaded.'}
    except Exception as e:
        return {'status': 'error', 'message': f'Error loading artifact {artifact_name}: {e!s}'}