"""'fetch_transcript' tool for FOMC Research sample agent"""
import logging
from google.adk.tools import ToolContext
from google.genai.types import Part
from ..shared_libraries import file_utils
logger = logging.getLogger(__name__)

async def fetch_transcript_tool(tool_context: ToolContext) -> dict:
    """Retrieves the Fed press conference transcript from the Fed website.

    Args:
      tool_context: ToolContext object.

    Returns:
      A dict with "status" and (optional) "error_message" keys.
    """
    fed_hostname = 'https://www.federalreserve.gov'
    transcript_url = tool_context.state['transcript_url']
    if not transcript_url.startswith('https'):
        transcript_url = fed_hostname + transcript_url
    pdf_path = await file_utils.download_file_from_url(transcript_url, 'transcript.pdf', tool_context)
    if pdf_path is None:
        logger.error('Failed to download PDF from URLs, aborting')
        return {'status': 'error', 'error_message': 'Failed to download PDFs from GCS'}
    text = await file_utils.extract_text_from_pdf_artifact(pdf_path, tool_context)
    filename = 'transcript_fulltext'
    version = await tool_context.save_artifact(filename=filename, artifact=Part(text=text))
    logger.info('Saved artifact %s, ver %i', filename, version)
    return {'status': 'ok'}