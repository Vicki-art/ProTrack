from app.helpers.file_helpers import save_file, rollback_files_saving
from sqlalchemy.exc import SQLAlchemyError
from app import models, exceptions
from app.helpers.db_helpers import project_and_user_status, get_doc_or_error
from app.services import projects_services

def upload_project_related_docs(project_id, files, current_user, db):

    created_docs = []
    saved_files = []

    try:
        for file in files:
            file_key, size = save_file(file)

            db_file = models.File(
                original_filename=file.filename,
                file_key=file_key,
                size=size,
                content_type=file.content_type,
                uploaded_by=current_user.id,
                general_purpose=False
            )

            db.add(db_file)
            db.flush()

            project_doc = models.ProjectDocument(
                project_id=project_id,
                file_id=db_file.id,
                added_by=current_user.id
            )

            db.add(project_doc)
            created_docs.append(db_file)
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

def get_project_related_docs(project_id, current_user, db):
    project, is_owner, is_participant = project_and_user_status(project_id, current_user, db)

    if not is_owner and is_participant is None:
        raise exceptions.ForbiddenActionError("You have no access")

    project_documents = []

    for doc in project.project_docs:
        project_documents.append(doc.file)

    return project_documents

def get_doc_by_id(doc_id, current_user, db):
    document = get_doc_or_error(doc_id, db)

    if document.to_delete:
        raise exceptions.NotFoundError("Document not found")

    if document.general_purpose:
        return document

    doc_in_proj = document.project_links

    for p in doc_in_proj:
        is_owner = p.project.owner_id == current_user.id
        is_participant = False
        for u in p.project.project_memberships:
            if current_user.id == u.user_id:
                is_participant = True
                break

        if is_owner or is_participant:
            break
    else:
        raise exceptions.ForbiddenActionError("You have no access")

    return document

def delete_doc_by_id(document_id, current_user, db):
    pass
    # document = get_doc_or_error(document_id, db)
    # is_general_purpose_doc = document.general_purpose
    # uploaded_by_current_user = document.uploaded_by == current_user.id
    # is_project_owner = False
    #
    # if is_general_purpose_doc and uploaded_by_current_user:
    #     try:
    #         document.to_delete = True
    #         db.commit()
    #     except SQLAlchemyError as e:
    #         raise exceptions.DatabaseError(detail=str(e))
    # else:
    #     doc_in_proj = document.project_links
    #     for p in doc_in_proj:
    #         is_owner = p.project.owner_id == current_user.id



