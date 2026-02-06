from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
import uuid
from typing import Literal
from google.adk.events.event import Event
from google.genai.types import Content
from pydantic import BaseModel, Field

class Request(BaseModel):
    """Represents the input for a chat request with optional configuration."""
    message: Content
    events: list[Event]
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    model_config = {'extra': 'allow'}

class Feedback(BaseModel):
    """Represents feedback for a conversation."""
    score: int | float
    text: str | None = ''
    invocation_id: str
    log_type: Literal['feedback'] = 'feedback'
    service_name: Literal['test-agent'] = 'test-agent'
    user_id: str = ''