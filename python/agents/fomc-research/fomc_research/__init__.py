"""Initialization functions for FOMC Research Agent."""
import logging
import os
loglevel = os.getenv('GOOGLE_GENAI_FOMC_AGENT_LOG_LEVEL', 'INFO')
numeric_level = getattr(logging, loglevel.upper(), None)
if not isinstance(numeric_level, int):
    raise ValueError(f'Invalid log level: {loglevel}')
logger = logging.getLogger(__package__)
logger.setLevel(numeric_level)
MODEL = os.getenv('GOOGLE_GENAI_MODEL')
if not MODEL:
    MODEL = 'gemini-2.5-flash'
from . import agent