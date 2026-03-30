from typing import List

from fastapi import UploadFile, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import models
from app.database.db import db_transaction
from app.exceptions import exceptions
from app.storage.file_helpers import (
    rollback_files_saving,
    get_file_size,
    validate_file_size_per_project
)
from app.storage.factory import get_storage
from app.database.db_helpers import (
    clean_up_docs,
    project_and_user_status,
    check_membership,
    get_project_or_error,
    get_doc_or_error,
    document_access_check
)


def upload_project_related_docs(
        project_id: int,
        docs: List[UploadFile],
        current_user: models.User,
        db: Session
) -> list[models.Document]:

    project = get_project_or_error(project_id, db)
    is_owner = project.owner_id == current_user.id
    is_participant = check_membership(project_id, current_user.id, db)

    if not is_owner and not is_participant:
        raise exceptions.ForbiddenActionError("Access denied")

    uploaded_files_bytes_sum = sum([get_file_size(doc) for doc in docs])

    validate_file_size_per_project(project.storage_used_bytes, uploaded_files_bytes_sum)

    created_docs = []
    saved_files = []
    storage = get_storage()

    with db_transaction(db, rollback_files_saving, saved_files, storage):
        for doc in docs:
            storage = get_storage()
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

    project, is_owner, is_participant = project_and_user_status(project_id, current_user, db)

    if not is_owner and is_participant is None:
        raise exceptions.ForbiddenActionError("You have no access")

    project_documents = [doc for doc in project.docs]

    return project_documents


def get_doc_by_id(
        doc_id: int,
        current_user: models.User,
        db: Session
) -> models.Document:

    document = get_doc_or_error(doc_id, db)
    full_access_allowed, access_as_project_participant = document_access_check(document, current_user.id, db)
    if not full_access_allowed and not access_as_project_participant:
        raise exceptions.ForbiddenActionError("You have no access")

    return document


def delete_doc_by_id(
        document_id: int,
        background_tasks: BackgroundTasks,
        current_user: models.User,
        db: Session
) -> None:

    document = get_doc_or_error(document_id, db)
    full_access_allowed, access_as_project_participant = document_access_check(document, current_user.id, db)
    if not full_access_allowed:
        if not access_as_project_participant:
            raise exceptions.ForbiddenActionError("You have no access")
        else:
            raise exceptions.ForbiddenActionError("Only project owner can delete related documents")

    deleted_file_key = document.file_key

    with db_transaction(db):
        document.to_delete = True
        document.project.storage_used_bytes -= document.size

    background_tasks.add_task(clean_up_docs, [deleted_file_key], storage=get_storage())

    return


def update_document_by_id(
        document_id: int,
        new_doc: UploadFile,
        background_tasks: BackgroundTasks,
        current_user: models.User,
        db: Session
) -> models.Document:
    document_to_change = get_doc_by_id(document_id, current_user, db)

    uploaded_file_bytes_size = get_file_size(new_doc)

    size_diff = uploaded_file_bytes_size - document_to_change.size

    validate_file_size_per_project(document_to_change.project.storage_used_bytes, size_diff)

    previous_file_version = document_to_change.file_key
    rollback_files = []

    storage = get_storage()

    with db_transaction(db, rollback_files_saving, rollback_files, storage):
        file_key, size = storage.save_file(new_doc)

        rollback_files.append(file_key)

        document_to_change.file_key = file_key
        document_to_change.original_filename = new_doc.filename
        document_to_change.size = size
        document_to_change.content_type = new_doc.content_type
        document_to_change.uploaded_by = current_user.id
        document_to_change.project.storage_used_bytes += size_diff


    background_tasks.add_task(storage.delete_file, previous_file_version)

    return document_to_change
