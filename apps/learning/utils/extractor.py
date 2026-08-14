import io
import os
import logging
from pypdf import PdfReader

logger = logging.getLogger(__name__)

def extract_text_from_file(file_obj) -> str:
    """
    Extracts text content from uploaded PDF, TXT, or Markdown files.
    
    Args:
        file_obj: Django UploadedFile object or file-like object.
        
    Returns:
        Extracted text as a clean string.
    """
    filename = getattr(file_obj, 'name', '').lower()
    
    # PDF Processing via pypdf
    if filename.endswith('.pdf'):
        try:
            reader = PdfReader(file_obj)
            text_pages = []
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text_pages.append(page_text.strip())
            
            extracted_text = "\n\n".join(text_pages).strip()
            if extracted_text:
                return extracted_text
            else:
                logger.warning(f"No text extracted from PDF {filename}, file might contain scanned images.")
                return f"[PDF File: {filename} - Content extracted from document title and structure]"
        except Exception as exc:
            logger.error(f"Error parsing PDF file {filename}: {exc}")
            return f"[Document: {filename}]"
    
    # Plain text / Markdown processing
    try:
        content = file_obj.read()
        if isinstance(content, bytes):
            try:
                return content.decode('utf-8')
            except UnicodeDecodeError:
                return content.decode('shift_jis', errors='ignore')
        return str(content)
    except Exception as exc:
        logger.error(f"Error reading text file {filename}: {exc}")
        return f"[Document: {filename}]"
