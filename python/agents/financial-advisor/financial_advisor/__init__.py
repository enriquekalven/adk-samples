"""Financial coordinator: provide reasonable investment strategies"""
import os
import google.auth
from . import agent
_, project_id = google.auth.default()
os.environ.setdefault('GOOGLE_CLOUD_PROJECT', project_id)
os.environ['GOOGLE_CLOUD_LOCATION'] = 'global'
os.environ.setdefault('GOOGLE_GENAI_USE_VERTEXAI', 'True')