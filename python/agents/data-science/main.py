from google.adk.agents.context_cache_config import ContextCacheConfig
from google.adk.agents.context_cache_config import ContextCacheConfig
'\nThis file initializes a FastAPI application for Data Science agent\nusing get_fast_api_app() from ADK. Session service URI and a flag\nfor a web interface configured via environment variables.\nIt can then be run using Uvicorn, which listens on a port specified by\nthe PORT environment variable or defaults to 8080.\nThis approach offers more flexibility, particularly if you want to\nembed Data Science agent within a custom FastAPI application.\nIt is used for Cloud Run deployment with standard gcloud run deploy command.\n'
import os
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app
from google.cloud import logging as google_cloud_logging
load_dotenv()
logging_client = google_cloud_logging.Client()
logger = logging_client.logger(__name__)
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
session_uri = os.getenv('SESSION_SERVICE_URI', None)
web_interface_enabled = os.getenv('SERVE_WEB_INTERFACE', 'False').lower() in ('true', '1')
app_args = {'agents_dir': AGENT_DIR, 'web': web_interface_enabled}
if session_uri:
    app_args['session_service_uri'] = session_uri
else:
    logger.log_text('SESSION_SERVICE_URI not provided. Using in-memory session service instead. All sessions will be lost when the server restarts.', severity='WARNING')
app: FastAPI = get_fast_api_app(**app_args)
app.title = 'data_science'
app.description = 'Data Science Agent'
if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', '8080')))