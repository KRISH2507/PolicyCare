import os
import uuid
import shutil
from fastapi import UploadFile, HTTPException, status

UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "json", "txt"}


def ensure_upload_dir():
    os.makedirs(UPLOAD_DIR, exist_ok=True)


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_upload(file: UploadFile) -> tuple[str, str]:
    ensure_upload_dir()
    if not allowed_file(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )
    ext = file.filename.rsplit(".", 1)[1].lower()
    file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}.{ext}")
    try:
        with open(file_path, "wb") as buf:
            shutil.copyfileobj(file.file, buf)
    except Exception:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to save file")
    return file_path, ext


def delete_file(path: str) -> bool:
    if os.path.exists(path):
        try:
            os.remove(path)
            return True
        except Exception:
            return False
    return False
