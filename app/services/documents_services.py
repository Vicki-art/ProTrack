from fastapi import UploadFile, BackgroundTasks
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import models, exceptions
from app.helpers.file_helpers import save_file, rollback_files_saving
from app.helpers.db_helpers import (
    clean_up_docs,
    delete_files,
    project_and_user_status,
    check_membership,
    get_project_or_error,
    get_doc_or_error,
    document_access_check
)

def upload_project_related_docs(
        project_id: int,
        docs: UploadFile,
        current_user: models.User,
        db: Session
) -> list[models.Document]:

    project = get_project_or_error(project_id, db)
    is_owner = project.owner_id == current_user.id
    is_participant = check_membership(project_id, current_user.id, db)

    if not is_owner and not is_participant:
        raise exceptions.ForbiddenActionError("Access denied")

    created_docs = []
    saved_files = []

    try:
        for doc in docs:
            file_key, size = save_file(doc)

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
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        rollback_files_saving(saved_files)
        raise exceptions.DatabaseError(detail=str(e))

    except Exception as e:
        db.rollback()
        rollback_files_saving(saved_files)
        raise

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

    try:
        document.to_delete = True
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise exceptions.DatabaseError(detail=str(e))

    background_tasks.add_task(clean_up_docs, [deleted_file_key])

    return

def update_document_by_id(
        document_id: int,
        new_doc: UploadFile,
        background_tasks: BackgroundTasks,
        current_user: models.User,
        db: Session
    ) -> models.Document:
    document_to_change = get_doc_by_id(document_id, current_user, db)


    previous_file_version = document_to_change.file_key
    print(previous_file_version)
    new_file_version = None

    try:
        file_key, size = save_file(new_doc)
        new_file_version = file_key
        print(new_file_version)
        document_to_change.file_key = file_key

        document_to_change.original_filename = new_doc.filename
        document_to_change.size = size
        document_to_change.content_type = new_doc.content_type,
        document_to_change.uploaded_by = current_user.id

        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        rollback_files_saving([new_file_version])
        raise exceptions.DatabaseError(detail=str(e))

    except Exception as e:
        db.rollback()
        rollback_files_saving([new_file_version])
        raise

    background_tasks.add_task(delete_files, previous_file_version)

    return document_to_change






