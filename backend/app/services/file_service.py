import os
import uuid
import shutil
from fastapi import UploadFile, HTTPException, status

UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "json", "txt"}

def ensure_upload_dir():
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def save_upload(file: UploadFile) -> tuple[str, str]:
    """
    Saves the file to the UPLOAD_DIR with a unique UUID filename.
    Returns: (file_path, file_extension)
    """
    ensure_upload_dir()
    if not allowed_file(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    ext = file.filename.rsplit(".", 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save file physically"
        )
        
    return file_path, ext

def delete_file(path: str) -> bool:
    """
    Deletes the physical file from the given path if it exists.
    """
    if os.path.exists(path):
        try:
            os.remove(path)
            return True
        except Exception:
            return False
    return False