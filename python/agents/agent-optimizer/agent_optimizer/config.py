"""Configuration module for the Agent Optimizer."""
import logging
import os
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class AgentModel(BaseModel):
    """Agent model settings."""
    name: str = Field(default='agent_optimizer')
    model: str = Field(default='gemini-2.0-flash')

class Config(BaseSettings):
    """Configuration settings for the customer service agent."""
    model_config = SettingsConfigDict(env_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), '../.env'), env_prefix='GOOGLE_', case_sensitive=True)
    agent_settings: AgentModel = Field(default=AgentModel())
    app_name: str = 'agent_optimizer_app'
    CLOUD_PROJECT: str = Field(default='project-maui')
    CLOUD_LOCATION: str = Field(default='global')
    GENAI_USE_VERTEXAI: str = Field(default='1')
    API_KEY: str | None = Field(default='')