import os
import google.auth
_, project_id = google.auth.default()
os.environ.setdefault('GOOGLE_CLOUD_PROJECT', project_id)
os.environ['GOOGLE_CLOUD_LOCATION'] = 'global'
os.environ.setdefault('GOOGLE_GENAI_USE_VERTEXAI', 'True')
import torch
torch.classes.__path__ = []
try:
    from .shared_libraries.init_env import init_env, webshop_env
except Exception:
    webshop_env = None
    init_env = None
from . import agent