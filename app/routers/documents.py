from fastapi import APIRouter, UploadFile, Depends, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core import schemas, oauth2
from app.database import models
from app.database.db import get_db
from app.services import documents_services
from app.storage.factory import get_storage

router = APIRouter()


@router.get(
    "/{document_id}",
    response_model=None,
    status_code=status.HTTP_200_OK
)
def get_document(
    document_id: int,
    current_user: models.User = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
) -> StreamingResponse:
    """
    Get document ingo by ID (can be performed by project owner or by participant)
    """
    doc = documents_services.get_doc_by_id(document_id, current_user, db)

    storage = get_storage()

    return storage.get_file_response(doc)


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_document(
    document_id: int,
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
) -> None:
    """
    Delete document by ID (can be performed by project owner)
    """
    documents_services.delete_doc_by_id(document_id, background_tasks, current_user, db)


@router.put(
    "/{document_id}",
    response_model=schemas.FilesOut,
    status_code=status.HTTP_200_OK
)
def update_document(
    document_id: int,
    new_doc: UploadFile,
    background_tasks: BackgroundTasks,
    current_user=Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
) -> schemas.FilesOut:
    """
    Update document by ID (can be performed by project owner or by participant)
    """

    new_doc = documents_services.update_document_by_id(
        document_id,
        new_doc,
        background_tasks,
        current_user,
        db
    )

    return new_doc
