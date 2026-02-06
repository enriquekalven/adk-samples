from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from google.adk.tools import ToolContext
from google.genai import types
from ..shared_libraries.init_env import get_webshop_env

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
async def click(button_name: str, tool_context: ToolContext) -> str:
    """Click the button with the given name.

    Args:
      button_name(str): The name of the button to click.
      tool_context(ToolContext): The function context.

    Returns:
      str: The webpage after clicking the button.
    """
    webshop_env = get_webshop_env()
    status = {'reward': None, 'done': False}
    action_string = f'click[{button_name}]'
    _, status['reward'], status['done'], _ = webshop_env.step(action_string)
    ob = webshop_env.observation
    index = ob.find('Back to Search')
    if index >= 0:
        ob = ob[index:]
    print('#' * 50)
    print('Click result:')
    print(f'status: {status}')
    print(f'observation: {ob}')
    print('#' * 50)
    if button_name == 'Back to Search':
        webshop_env.server.assigned_instruction_text = 'Back to Search'
    try:
        await tool_context.save_artifact('html', types.Part.from_uri(file_uri=webshop_env.state['html'], mime_type='text/html'))
    except ValueError as e:
        print(f'Error saving artifact: {e}')
    return ob