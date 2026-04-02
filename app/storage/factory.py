from app.core.config import settings
from app.storage.s3 import S3Storage
from app.storage.local import LocalStorage

def get_storage():
    if settings.USE_S3:
        return S3Storage()
    return LocalStorage()