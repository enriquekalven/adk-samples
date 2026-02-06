from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
import os
from pathlib import Path
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

class Config:

    @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
    def __init__(self):
        self.project_id: str | None = os.getenv('GOOGLE_CLOUD_PROJECT') or os.getenv('GCP_PROJECT_ID')
        self.location: str | None = os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1').lower()
        self.use_vertex_ai: bool = os.getenv('GOOGLE_GENAI_USE_VERTEXAI', '0') == '1'
        self.root_agent_model: str = os.getenv('ROOT_AGENT_MODEL', 'gemini-2.5-pro')
        self.repository_name: str = os.getenv('DATAFORM_REPOSITORY_NAME', 'default-repository')
        self.workspace_name: str = os.getenv('DATAFORM_WORKSPACE_NAME', 'default-workspace')

    def validate(self) -> bool:
        """Validate that all required configuration is present."""
        if not self.project_id:
            raise ValueError('GOOGLE_CLOUD_PROJECT environment variable is required')
        return True

    @property
    def project_location(self) -> str:
        """Get the project location in the format required by BigQuery and Dataform."""
        return f'{self.project_id}.{self.location}'

    @property
    def vertex_project_location(self) -> str:
        """Get the project location in the format required by Vertex AI."""
        return f'{self.project_id}.{self.location}'
config = Config()