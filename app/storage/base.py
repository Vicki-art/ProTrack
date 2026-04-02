from abc import ABC, abstractmethod
from fastapi import UploadFile

class BaseStorage(ABC):

    @abstractmethod
    def get_file_response(self, document):
        pass

    @abstractmethod
    def save_file(self, file: UploadFile) -> tuple[str, int]:
        pass

    @abstractmethod
    def delete_file(self, file_key: str) -> None:
        pass