from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
import io
import logging
import os
import warnings
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from google.cloud import storage
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
warnings.filterwarnings('ignore')
STORAGE_BUCKET = os.getenv('REPORT_STORAGE_BUCKET')
logger = logging.getLogger(__name__)
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
REPORT_DOCUMENT_FILE_NAME = f'pre_authorization_report_{timestamp}.pdf'

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def store_pdf(pdf_text: str) -> str:
    """Writes text to a PDF file, then uploads it to Google Cloud Storage.
    Args:
        pdf_text: The text to write to the PDF.
    """
    pdf_buffer = None
    try:
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        for paragraph_text in pdf_text.split('\n\n'):
            if paragraph_text.strip():
                p = Paragraph(paragraph_text.strip().replace('\n', '<br/>'), styles['Normal'])
                story.append(p)
                story.append(Spacer(1, 0.05 * letter[1]))
        doc.build(story)
        pdf_buffer.seek(0)
        storage_client = storage.Client()
        bucket = storage_client.bucket(STORAGE_BUCKET)
        blob = bucket.blob(REPORT_DOCUMENT_FILE_NAME)
        blob.upload_from_file(pdf_buffer, content_type='application/pdf')
        logger.info(f'Successfully uploaded PDF to gs://{STORAGE_BUCKET}/{REPORT_DOCUMENT_FILE_NAME}')
        return f'Successfully uploaded PDF to gs://{STORAGE_BUCKET}/{REPORT_DOCUMENT_FILE_NAME}'
    except Exception as e:
        logger.error(f'Error writing text to PDF and uploading: {e}')
        raise
    finally:
        if pdf_buffer:
            pdf_buffer.close()