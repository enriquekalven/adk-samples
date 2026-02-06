import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)
if os.getenv('GOOGLE_API_KEY'):
    os.environ.setdefault('GOOGLE_GENAI_USE_VERTEXAI', 'False')
else:
    import google.auth
    _, project_id = google.auth.default()
    os.environ.setdefault('GOOGLE_CLOUD_PROJECT', project_id)
    os.environ['GOOGLE_CLOUD_LOCATION'] = 'global'
    os.environ.setdefault('GOOGLE_GENAI_USE_VERTEXAI', 'True')

@dataclass
class ResearchConfiguration:
    """Configuration for research-related models and parameters.

    Attributes:
        critic_model (str): Model for evaluation tasks.
        worker_model (str): Model for working/generation tasks.
        max_search_iterations (int): Maximum search iterations allowed.
    """
    critic_model: str = 'gemini-3-pro-preview'
    worker_model: str = 'gemini-3-pro-preview'
    max_search_iterations: int = 5
config = ResearchConfiguration()