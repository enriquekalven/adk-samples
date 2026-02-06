import os
from dataclasses import dataclass
import google.auth
_, project_id = google.auth.default()
os.environ.setdefault('GOOGLE_CLOUD_PROJECT', project_id)
os.environ.setdefault('GOOGLE_CLOUD_LOCATION', 'global')
os.environ.setdefault('GOOGLE_GENAI_USE_VERTEXAI', 'True')

@dataclass
class SecurityAuditConfig:
    """Configuration for red team security models and parameters.

    Attributes:
        evaluator_model: The model used for evaluating security vulnerabilities.
        red_team_model: The model used for generating red team attacks.
        target_model: The target model being audited for security vulnerabilities.
    """
    evaluator_model: str = 'gemini-2.5-pro'
    red_team_model: str = 'gemini-2.5-pro'
    target_model: str = 'gemini-2.5-flash'
config = SecurityAuditConfig()