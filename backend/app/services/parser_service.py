import fitz  # PyMuPDF
import json
from typing import List, Dict

def parse_pdf(file_path: str) -> List[Dict]:
    """Extracts text from a PDF, preserving exactly which page each block came from."""
    pages = []
    try:
        with fitz.open(file_path) as doc:
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                # Ensure spacing is somewhat preserved securely 
                text = page.get_text("text").strip()
                if text:
                    pages.append({"page": page_num + 1, "text": text})
    except Exception as e:
        raise ValueError(f"Failed to parse PDF: {str(e)}")
    return pages

def parse_txt(file_path: str) -> List[Dict]:
    """Reads a flat text file and registers it entirely as 'page 1'."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read().strip()
        if not text:
            return []
        return [{"page": 1, "text": text}]
    except Exception as e:
        raise ValueError(f"Failed to parse TXT: {str(e)}")

def parse_json(file_path: str) -> List[Dict]:
    """Loads a JSON object and dumps it into a readable formatted string as 'page 1'."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        text = json.dumps(data, indent=2).strip()
        return [{"page": 1, "text": text}]
    except Exception as e:
        raise ValueError(f"Failed to parse JSON: {str(e)}")

def extract_document_text(file_path: str, file_type: str) -> List[Dict]:
    """Universal router mapping file types to their specialized parsing functions."""
    if file_type == "pdf":
        return parse_pdf(file_path)
    elif file_type == "txt":
        return parse_txt(file_path)
    elif file_type == "json":
        return parse_json(file_path)
    else:
        raise ValueError(f"Unsupported file type for parsing: {file_type}")