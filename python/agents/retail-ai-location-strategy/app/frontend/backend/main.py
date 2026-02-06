from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
'FastAPI server wrapping ADK agent with AG-UI middleware.\n\nThis server provides an AG-UI compatible endpoint that wraps the existing\nLocationStrategyPipeline agent without modifying any core agent files.\n\nUsage:\n    cd app/frontend/backend\n    pip install -r requirements.txt\n    python main.py\n\n    # Or with uv:\n    uv pip install -r requirements.txt\n    uv run python main.py\n'
import os
import sys
from pathlib import Path
import uvicorn
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.agent import root_agent
app_dir = Path(__file__).parent.parent.parent
project_root = app_dir.parent
sys.path.insert(0, str(project_root))
env_path = app_dir / '.env'
if env_path.exists():
    load_dotenv(env_path)
adk_agent = ADKAgent(adk_agent=root_agent, app_name='retail_location_strategy', user_id='demo_user', execution_timeout_seconds=1800, tool_timeout_seconds=600)
app = FastAPI(title='Retail Location Strategy API', description='AG-UI compatible API for the Retail AI Location Strategy agent', version='1.0.0')
app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:3000', 'http://127.0.0.1:3000'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])

@app.get('/health')
async def health_check():
    """Health check endpoint."""
    return {'status': 'healthy', 'agent': 'LocationStrategyPipeline'}
add_adk_fastapi_endpoint(app, adk_agent, path='/')
if __name__ == '__main__':
    port = int(os.environ.get('PORT', '8000'))
    print(f'Starting AG-UI server at http://0.0.0.0:{port}')
    print('Frontend should connect to this URL')
    uvicorn.run(app, host='0.0.0.0', port=port)