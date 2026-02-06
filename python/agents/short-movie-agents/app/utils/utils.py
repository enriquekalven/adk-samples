import logging
import os
logger = logging.getLogger(__name__)
PROMPTS_PATH = '../prompts/'

def load_prompt_from_file(filename: str, default_instruction: str='Default instruction.') -> str:
    """Reads instruction text from a file relative to this script."""
    instruction = default_instruction
    try:
        filepath = os.path.join(os.path.dirname(__file__), PROMPTS_PATH, filename)
        with open(filepath, encoding='utf-8') as f:
            instruction = f.read()
        logger.info(f'Successfully loaded instruction from {filename}')
    except FileNotFoundError:
        logger.warning(f'WARNING: Instruction file not found: {filepath}. Using default.')
    except Exception as e:
        logger.error(f'ERROR loading instruction file {filepath}: {e}. Using default.')
    return instruction