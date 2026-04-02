import logging

from fastapi import UploadFile

from app.exceptions import exceptions
from app.storage.base import BaseStorage

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".docs", ".txt"}
MAX_PROJECT_DOCS_VOLUME = 1024 * 500

logger = logging.getLogger(__name__)

def rollback_files_saving(
        saved_files: list[str],
        storage: BaseStorage,
) -> None:

    for file_key in saved_files:
        try:
            storage.delete_file(file_key)
        except Exception:
            logger.exception(
                "Rollback failed for file",
                extra={"file_key": file_key}
            )

def validate_file_ext(ext: str) -> None:
    if ext not in ALLOWED_EXTENSIONS:
        raise exceptions.ValidationError(f"Forbidden file extension: {ext}")


def validate_file_size_per_project(current_size, uploaded_size):
    if current_size + uploaded_size > MAX_PROJECT_DOCS_VOLUME:
        raise exceptions.ValidationError("Too big amount of documents per project")


def get_file_size(file: UploadFile) -> int:
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    return size


def format_file_size(size_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024