from typing import List

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.database import models
from app.database.db import db_transaction
from app.storage.file_helpers import (
    rollback_files_saving,
    get_file_size,
    validate_file_size_per_project
)
from app.storage.base import BaseStorage
from app.database.db_helpers import (
    get_project_or_error,
    get_doc_or_error,
    check_project_access,
    check_project_access_allow_only_for_owner
)


def upload_project_related_docs(
        project_id: int,
        docs: List[UploadFile],
        current_user: models.User,
        db: Session,
        storage: BaseStorage
) -> list[models.Document]:
    """
    Upload multiple documents to a project.

    Checks:
    - User must be project owner or participant
    - Project storage limits must not be exceeded

    Behavior:
    - Saves files to storage
    - Creates DB records for each file
    - Updates project storage usage
    - Rolls back DB and storage changes on failure

    Returns:
        List of created Document objects
    """

    project = get_project_or_error(project_id, db)

    check_project_access(project, current_user, db, allow_participant=True)

    uploaded_files_bytes_sum = sum([get_file_size(doc) for doc in docs])

    validate_file_size_per_project(project.storage_used_bytes, uploaded_files_bytes_sum)

    created_docs = []
    saved_files = []

    with db_transaction(db, rollback_files_saving, saved_files, storage):
        for doc in docs:
            file_key, size = storage.save_file(doc)

            db_doc = models.Document(
                original_filename=doc.filename,
                file_key=file_key,
                size=size,
                content_type=doc.content_type,
                project_id=project_id,
                uploaded_by=current_user.id
            )

            db.add(db_doc)
            db.flush()
            created_docs.append(db_doc)
            saved_files.append(file_key)
        project.storage_used_bytes += uploaded_files_bytes_sum

    return created_docs


def get_project_related_docs(
        project_id: int,
        current_user: models.User,
        db: Session
) -> list[models.Document]:
    """
    Retrieve all documents for a project.

    Access:
    - Allowed for project owner
    - Allowed for project participants

    Raises:
        ForbiddenActionError: if user has no access

    Returns:
        List of project documents
    """
    project = get_project_or_error(project_id, db)
    check_project_access(project, current_user, db, allow_participant=True)

    return list(project.docs)


def get_doc_by_id(
        doc_id: int,
        current_user: models.User,
        db: Session
) -> models.Document:
    """
    Retrieve a document by ID.

    Access:
    - Project owner has full access
    - Project participants may have limited access depending on project rules

    Raises:
        ForbiddenActionError: if user has no access

    Returns:
        Document instance
    """
    document = get_doc_or_error(doc_id, db)
    check_project_access(document.project, current_user, db, allow_participant=True)

    return document


def delete_doc_by_id(
        document_id: int,
        current_user: models.User,
        db: Session,
) -> str:
    """
    Mark a document for deletion and update project storage usage.

    Access rules:
    - Project owner: full delete access
    - Participants: not allowed to delete

    Behavior:
    - Marks document as deleted (soft delete)
    - Decreases project storage counter
    - Returns file key for async storage cleanup

    Returns:
        File key that must be removed from storage
    """

    document = get_doc_or_error(document_id, db)
    check_project_access_allow_only_for_owner(document.project, current_user, db)

    deleted_file_key = document.file_key

    with db_transaction(db):
        document.to_delete = True
        document.project.storage_used_bytes -= document.size

    return deleted_file_key


def update_document_by_id(
        document_id: int,
        new_doc: UploadFile,
        current_user: models.User,
        db: Session,
        storage: BaseStorage
) -> tuple[models.Document, str]:
    """
    Replace an existing document with a new file version.

    Checks:
    - User must have access to the document
    - Project storage limits must not be exceeded after update

    Behavior:
    - Uploads new file to storage
    - Updates DB record with new metadata
    - Adjusts project storage usage
    - Old file is returned for async cleanup
    - Rolls back DB/storage changes on failure

    Returns:
        Tuple of:
        - Updated Document
        - Old file key for deletion
    """
    document_to_change = get_doc_by_id(document_id, current_user, db)

    uploaded_file_bytes_size = get_file_size(new_doc)

    size_diff = uploaded_file_bytes_size - document_to_change.size

    validate_file_size_per_project(document_to_change.project.storage_used_bytes, size_diff)

    previous_file_version = document_to_change.file_key
    rollback_files = []

    with db_transaction(db, rollback_files_saving, rollback_files, storage):
        file_key, size = storage.save_file(new_doc)

        rollback_files.append(file_key)

        document_to_change.file_key = file_key
        document_to_change.original_filename = new_doc.filename
        document_to_change.size = size
        document_to_change.content_type = new_doc.content_type
        document_to_change.uploaded_by = current_user.id
        document_to_change.project.storage_used_bytes += size_diff

    return document_to_change, previous_file_version
