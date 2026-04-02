import uuid
import os
import logging

from fastapi import UploadFile
from fastapi.responses import FileResponse

from app.storage.base import BaseStorage
from app.core.config import settings
from app.storage.file_helpers import validate_file_ext

logger = logging.getLogger(__name__)


class LocalStorage(BaseStorage):

    def get_file_response(self, document):
        file_path = os.path.join(settings.UPLOAD_DIR, document.file_key)

        return FileResponse(
            path=file_path,
            media_type=document.content_type,
            filename=document.original_filename
        )

    def save_file(self, file: UploadFile) -> tuple[str, int]:
        ext = os.path.splitext(file.filename)[1].lower()

        validate_file_ext(ext)

        file_key_uuid = str(uuid.uuid4())

        file_key = f"uploads/{file_key_uuid}{ext}"
        file_path = os.path.join(settings.UPLOAD_DIR, file_key)

        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        size = 0
        with open(file_path, "wb") as f:
            while chunk := file.file.read(1024 * 1024):
                size += len(chunk)
                f.write(chunk)

        return file_key, size

    def delete_file(self, file_to_delete_key: str) -> None:
        file_path = os.path.join(settings.UPLOAD_DIR, file_to_delete_key)
        try:
            os.remove(file_path)
        except FileNotFoundError as e:
            logger.warning(
                "File not found during deletion",
                extra={"file_path": file_path},
            )
        except Exception:
            logger.exception(
                "Unexpected error while deleting file",
                extra={"file_path": file_path},
            )

