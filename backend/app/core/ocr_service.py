"""
OCR Service - Tesseract (Free)
Extract text from receipt images
"""
import os
import pytesseract
from PIL import Image
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Set Tesseract path for Windows
tesseract_path = os.getenv("TESSERACT_PATH", "C:\\Program Files\\Tesseract-OCR\\tesseract.exe")
pytesseract.pytesseract.tesseract_cmd = tesseract_path


class OCRService:
    """Free Tesseract OCR Service"""
    
    def __init__(self):
        self.lang = os.getenv("OCR_LANG", "eng")
    
    def extract_text_from_image(self, image_path: str) -> str:
        """
        Extract text from receipt image using Tesseract
        """
        try:
            # Verify file exists
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image not found: {image_path}")
            
            # Open and process image
            image = Image.open(image_path)
            
            # Preprocessing for better OCR (grayscale + threshold)
            image = image.convert('L')  # Grayscale
            
            # Extract text
            text = pytesseract.image_to_string(image, lang=self.lang)
            
            logger.info(f"OCR completed: {len(text)} characters extracted")
            return text.strip()
            
        except Exception as e:
            logger.error(f"OCR failed: {str(e)}")
            raise Exception(f"OCR processing failed: {str(e)}")
    
    def extract_text_from_bytes(self, image_bytes: bytes) -> str:
        """
        Extract text from image bytes (for uploaded files)
        """
        try:
            from io import BytesIO
            image = Image.open(BytesIO(image_bytes))
            image = image.convert('L')
            text = pytesseract.image_to_string(image, lang=self.lang)
            return text.strip()
        except Exception as e:
            logger.error(f"OCR from bytes failed: {str(e)}")
            raise Exception(f"OCR processing failed: {str(e)}")

# Singleton instance
ocr_service = OCRService()