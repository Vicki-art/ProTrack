from fastapi import APIRouter, UploadFile, Depends, status, BackgroundTasks, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core import schemas, oauth2
from app.database import models
from app.database.db import get_db
from app.services import documents_services
from app.storage.factory import get_storage
from app.database.db_helpers import clean_up_docs
from app.storage.base import BaseStorage

router = APIRouter()


@router.get(
    "/{document_id}",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="Download document",
    description="Retrieve and stream a document by its ID. Accessible by project owner and participants."
)
def get_document(
    document_id: int,
    current_user: models.User = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db),
    storage: BaseStorage = Depends(get_storage)
) -> StreamingResponse:

    doc = documents_services.get_doc_by_id(document_id, current_user, db)

    return storage.get_file_response(doc)


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete document",
    description="Delete a document by its ID. Only project owner is allowed to perform this action."
)
def delete_document(
    document_id: int,
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db),
    storage: BaseStorage = Depends(get_storage)
) -> None:

    file_key_to_delete = documents_services.delete_doc_by_id(
        document_id,
        current_user,
        db
    )

    background_tasks.add_task(
        clean_up_docs,
        [file_key_to_delete],
        storage
    )


@router.put(
    "/{document_id}",
    response_model=schemas.FilesOut,
    status_code=status.HTTP_200_OK,
    summary="Update document",
    description="Replace an existing document with a new file. Accessible by project owner and participants."
)
def update_document(
    document_id: int,
    background_tasks: BackgroundTasks,
    new_doc: UploadFile = File(...),
    current_user: models.User = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db),
    storage: BaseStorage = Depends(get_storage)
) -> schemas.FilesOut:

    updated_doc, file_key_to_delete = documents_services.update_document_by_id(
        document_id,
        new_doc,
        current_user,
        db,
        storage
    )

    background_tasks.add_task(
        clean_up_docs,
        [file_key_to_delete],
        storage
    )

    return updated_doc
