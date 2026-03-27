import logging
import os
import uuid

from fastapi import UploadFile

UPLOAD_DIR = "storage"

logger = logging.getLogger(__name__)

def save_file(file: UploadFile):
    ext = os.path.splitext(file.filename)[1].lower()
    file_key_uuid = str(uuid.uuid4())

    file_key = f"uploads/{file_key_uuid}{ext}"
    file_path = os.path.join(UPLOAD_DIR, file_key)

    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    size = 0
    with open(file_path, "wb") as f:
        while chunk := file.file.read(1024 * 1024):
            size += len(chunk)
            f.write(chunk)

    return file_key, size

def rollback_files_saving(saved_files: list):
    for _, file_key in saved_files:
        file_path = os.path.join(UPLOAD_DIR, file_key)
        if os.path.exists(file_path):
            os.remove(file_path)
    return

def delete_files(file_to_delete_key: str) -> None:

    file_path = os.path.join(UPLOAD_DIR, file_to_delete_key)

    try:
        os.remove(file_path)
    except FileNotFoundError as e:
        logger.exception(
            "Background task failed: delete_files",
            extra={"file_paths": file_path},
        )
    except Exception:
        logger.exception(
            "Unexpected error while deleting file",
            extra={"file_path": file_path},
        )
    return
