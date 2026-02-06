"""Configuration for Retail AI Location Strategy ADK Agent.

This agent supports both Google AI Studio and Vertex AI authentication modes.

For LOCAL DEVELOPMENT (AI Studio):
    GOOGLE_API_KEY=your_google_api_key
    GOOGLE_GENAI_USE_VERTEXAI=FALSE
    MAPS_API_KEY=your_maps_api_key

For PRODUCTION DEPLOYMENT (Vertex AI):
    GOOGLE_CLOUD_PROJECT=your-project-id
    GOOGLE_CLOUD_LOCATION=us-central1
    GOOGLE_GENAI_USE_VERTEXAI=TRUE
    MAPS_API_KEY=your_maps_api_key
"""
import os
from pathlib import Path
from dotenv import load_dotenv
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)
USE_VERTEX_AI = os.environ.get('GOOGLE_GENAI_USE_VERTEXAI', 'FALSE').upper() == 'TRUE'
if USE_VERTEX_AI:
    GOOGLE_CLOUD_PROJECT = os.environ.get('GOOGLE_CLOUD_PROJECT', '')
    GOOGLE_CLOUD_LOCATION = os.environ.get('GOOGLE_CLOUD_LOCATION', 'us-central1')
    GOOGLE_API_KEY = ''
else:
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY', '')
    GOOGLE_CLOUD_PROJECT = ''
    GOOGLE_CLOUD_LOCATION = ''
MAPS_API_KEY = os.environ.get('MAPS_API_KEY', '')
FAST_MODEL = 'gemini-2.5-pro'
PRO_MODEL = 'gemini-2.5-pro'
CODE_EXEC_MODEL = 'gemini-2.5-pro'
IMAGE_MODEL = 'gemini-3-pro-image-preview'
RETRY_INITIAL_DELAY = 5
RETRY_ATTEMPTS = 5
RETRY_MAX_DELAY = 60
APP_NAME = 'retail_location_strategy'