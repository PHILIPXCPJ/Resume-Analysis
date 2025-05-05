import fitz  # PyMuPDF
from docx import Document
import textract
import os
import re
from typing import Optional

class FileParser:
    @staticmethod
    def extract_text(filepath: str) -> Optional[str]:
        """Extract text from various file formats"""
        try:
            ext = os.path.splitext(filepath)[1].lower()
            
            if ext == '.pdf':
                return FileParser._extract_from_pdf(filepath)
            elif ext == '.docx':
                return FileParser._extract_from_docx(filepath)
            elif ext == '.doc':
                return FileParser._extract_from_doc(filepath)
            elif ext == '.txt':
                return FileParser._extract_from_txt(filepath)
            else:
                # Try textract as fallback
                return FileParser._extract_with_textract(filepath)
                
        except Exception as e:
            raise ValueError(f"Could not parse file {filepath}: {str(e)}")

    @staticmethod
    def _extract_from_pdf(filepath: str) -> str:
        """Extract text from PDF while preserving some structure"""
        with fitz.open(filepath) as doc:
            text = ""
            for page in doc:
                text += page.get_text("text") + "\n"
            return text

    @staticmethod
    def _extract_from_docx(filepath: str) -> str:
        """Extract text from DOCX files"""
        doc = Document(filepath)
        return "\n".join([para.text for para in doc.paragraphs])

    @staticmethod
    def _extract_from_doc(filepath: str) -> str:
        """Extract text from old DOC format"""
        return textract.process(filepath).decode('utf-8')

    @staticmethod
    def _extract_from_txt(filepath: str) -> str:
        """Extract text from plain text files"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

    @staticmethod
    def _extract_with_textract(filepath: str) -> str:
        """Fallback text extraction using textract"""
        try:
            text = textract.process(filepath).decode('utf-8')
            # Clean up any binary characters that might remain
            text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\xff]', ' ', text)
            return text
        except Exception as e:
            raise ValueError(f"Textract failed to parse file: {str(e)}")