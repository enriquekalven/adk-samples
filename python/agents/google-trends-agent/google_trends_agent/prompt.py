from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
import os
from jinja2 import Environment, FileSystemLoader

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def load_few_shot_examples() -> str:
    """Loads and renders the Google Trends few-shot examples template.

    Returns:
        str: The rendered template with populated values.
    """
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_dir = os.path.join(current_dir, 'prompt-template')
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template('google_trends_few_shots.j2')
        rendered_template = template.render()
        return rendered_template
    except Exception as e:
        print(f'Error loading few-shot examples template: {e!s}')
        raise

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def load_table_structure_prompt() -> str:
    """Loads and renders the Google Trends table structure and rules template.

    Returns:
        str: The rendered template content.
    """
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_dir = os.path.join(current_dir, 'prompt-template')
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template('google_trends_table_structure.j2')
        return template.render()
    except Exception as e:
        print(f'Error loading table structure template: {e!s}')
        raise

def load_agent_instructions():
    """Dynamically loads agent instructions and few-shot examples."""
    try:
        table_structure_prompt = load_table_structure_prompt()
        few_shot_examples = load_few_shot_examples()
        full_instruction = f'{table_structure_prompt}\n\n{few_shot_examples}'
        print('Successfully loaded agent instructions.')
        return full_instruction
    except Exception as e:
        print(f'FATAL: Could not load agent instructions: {e}')
        return 'You are an agent that can query Google Trends data.'