import fitz
import json
from typing import List, Dict


def parse_pdf(file_path: str) -> List[Dict]:
    pages = []
    try:
        with fitz.open(file_path) as doc:
            for i, page in enumerate(doc):
                text = page.get_text("text").strip()
                if text:
                    pages.append({"page": i + 1, "text": text})
    except Exception as e:
        raise ValueError(f"Failed to parse PDF: {e}")
    return pages


def parse_txt(file_path: str) -> List[Dict]:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read().strip()
        return [{"page": 1, "text": text}] if text else []
    except Exception as e:
        raise ValueError(f"Failed to parse TXT: {e}")


def parse_json(file_path: str) -> List[Dict]:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [{"page": 1, "text": json.dumps(data, indent=2)}]
    except Exception as e:
        raise ValueError(f"Failed to parse JSON: {e}")


def extract_document_text(file_path: str, file_type: str) -> List[Dict]:
    if file_type == "pdf":
        return parse_pdf(file_path)
    elif file_type == "txt":
        return parse_txt(file_path)
    elif file_type == "json":
        return parse_json(file_path)
    raise ValueError(f"Unsupported file type: {file_type}")
