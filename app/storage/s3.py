import os
import uuid
import logging
import boto3

from fastapi import UploadFile
from fastapi.responses import StreamingResponse

from app.core.config import settings
from app.storage.base import BaseStorage
from app.storage.file_helpers import validate_file_ext

logger = logging.getLogger(__name__)


class S3Storage(BaseStorage):

    def __init__(self):
        self.client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        self.bucket = settings.S3_BUCKET


    def get_file_response(self, document):
        obj = self.client.get_object(
            Bucket=self.bucket,
            Key=document.file_key
        )

        return StreamingResponse(
            obj["Body"],
            media_type=document.content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{document.original_filename}"'
            }
        )


    def save_file(self, file: UploadFile) -> tuple[str, int]:
        ext = os.path.splitext(file.filename)[1].lower()
        validate_file_ext(ext)
        file_key = f"uploads/{uuid.uuid4()}{ext}"

        try:

            size = self._get_file_size(file)

            file.file.seek(0)

            self.client.upload_fileobj(
                file.file,
                self.bucket,
                file_key,
                ExtraArgs={
                    "ContentType": file.content_type
                }
            )

            logger.info(
                "File uploaded to S3",
                extra={"file_key": file_key}
            )

            return file_key, size

        except Exception as e:
            logger.exception(
                "Failed to upload file to S3",
                extra={"file_key": file_key}
            )
            raise

    def delete_file(self, file_key: str) -> None:
        try:
            self.client.delete_object(
                Bucket=self.bucket,
                Key=file_key
            )

            logger.debug(
                "File deleted from S3",
                extra={"file_key": file_key}
            )

        except Exception:
            logger.exception(
                "Unexpected error while deleting file from S3",
                extra={"file_key": file_key}
            )
            raise

    def _get_file_size(self, file: UploadFile) -> int:
        file.file.seek(0, os.SEEK_END)
        size = file.file.tell()
        file.file.seek(0)
        return size