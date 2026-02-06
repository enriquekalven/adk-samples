from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
import os
import google.auth
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app
from google.cloud import logging as google_cloud_logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider, export
from app.utils.gcs import create_bucket_if_not_exists
from app.utils.tracing import CloudTraceLoggingSpanExporter
from app.utils.typing import Feedback
_, project_id = google.auth.default()
logging_client = google_cloud_logging.Client()
logger = logging_client.logger(__name__)
allow_origins = os.getenv('ALLOW_ORIGINS', '').split(',') if os.getenv('ALLOW_ORIGINS') else None
bucket_name = f'gs://{project_id}-short-movie-agents-logs-data'
create_bucket_if_not_exists(bucket_name=bucket_name, project=project_id, location='europe-west4')
provider = TracerProvider()
processor = export.BatchSpanProcessor(CloudTraceLoggingSpanExporter())
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)
AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
session_service_uri = None
app: FastAPI = get_fast_api_app(agents_dir=AGENT_DIR, web=True, artifact_service_uri=bucket_name, allow_origins=allow_origins, session_service_uri=session_service_uri)
app.title = 'short-movie-agents'
app.description = 'API for interacting with the short-movie-agents'

@app.post('/feedback')
def collect_feedback(feedback: Feedback) -> dict[str, str]:
    """Collect and log feedback.

    Args:
        feedback: The feedback data to log

    Returns:
        Success message
    """
    logger.log_struct(feedback.model_dump(), severity='INFO')
    return {'status': 'success'}
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)