from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from google.adk.tools import ToolContext
from google.genai import types
from ..shared_libraries.init_env import get_webshop_env

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
async def search(keywords: str, tool_context: ToolContext) -> str:
    """Search for keywords in the webshop.

    Args:
      keywords(str): The keywords to search for.
      tool_context(ToolContext): The function context.

    Returns:
      str: The search result displayed in a webpage.
    """
    webshop_env = get_webshop_env()
    status = {'reward': None, 'done': False}
    action_string = f'search[{keywords}]'
    webshop_env.server.assigned_instruction_text = f'Find me {keywords}.'
    print(f'env instruction_text: {webshop_env.instruction_text}')
    _, status['reward'], status['done'], _ = webshop_env.step(action_string)
    ob = webshop_env.observation
    index = ob.find('Back to Search')
    if index >= 0:
        ob = ob[index:]
    print('#' * 50)
    print('Search result:')
    print(f'status: {status}')
    print(f'observation: {ob}')
    print('#' * 50)
    try:
        await tool_context.save_artifact('html', types.Part.from_uri(file_uri=webshop_env.state['html'], mime_type='text/html'))
    except ValueError as e:
        print(f'Error saving artifact: {e}')
    return ob