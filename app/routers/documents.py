from fastapi import APIRouter, UploadFile, File, Depends, status
from app import schemas
from sqlalchemy.orm import Session
from typing import List
from app.db import get_db
from app import oauth2
from app.services import documents_services


router = APIRouter()

@router.get("/{document_id}", response_model=schemas.FilesOut, status_code=status.HTTP_200_OK)
def get_document(
    document_id: int,
    current_user=Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)):
    doc = documents_services.get_doc_by_id(document_id, current_user, db)

    return doc

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    current_user=Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)):
    doc = documents_services.delete_doc_by_id(document_id, current_user, db)

    return

# @router.post("/projects/{project_id}/documents", status_code=status.HTTP_201_CREATED)
# async def upload_project_documents(
#     project_id: int,
#     files: List[UploadFile] = File(...),
#     current_user=Depends(oauth2.get_current_user),
#     db: Session = Depends(get_db)):
#
#     project_docs = documents_services.upload_project_docs(project_id, files, current_user, db)
#
#     return {"message": f"{len(project_docs)} doc(s) were downloaded"}