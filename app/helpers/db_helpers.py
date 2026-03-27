from typing import Tuple

from sqlalchemy.orm import Session

from app import models, exceptions, db
from app.helpers.file_helpers import delete_files


def get_project_or_error(
        project_id: int,
        db: Session
) -> models.Project:

    project: models.Project | None = db.query(models.Project).filter(
        models.Project.id == project_id
    ).first()

    if not project:
        raise exceptions.NotFoundError("Project not found")

    return project


def get_user_or_error(
        user_id: int,
        db: Session
) -> models.User:

    user: models.User | None  = db.query(models.User).filter(
        models.User.id == user_id
    ).first()

    if not user:
        raise exceptions.NotFoundError("User not found")

    return user


def get_user_by_username_or_error(
        username: str,
        db: Session
) -> models.User:

    user: models.User | None = db.query(models.User).filter(
        models.User.username == username
    ).first()

    if not user:
        raise exceptions.NotFoundError("User not found")

    return user


def check_membership(
    project_id: int,
    user_id: int,
    db: Session
) -> models.UserProject:

    membership: models.UserProject | None = db.query(models.UserProject).filter(
        models.UserProject.user_id == user_id,
        models.UserProject.project_id == project_id

    ).first()

    return membership

def project_and_user_status(
        project_id: int,
        user: models.User,
        db: Session
) -> Tuple[models.Project, bool, models.UserProject]:

    project = get_project_or_error(project_id, db)
    is_owner = user.id == project.owner_id
    is_participant = check_membership(project_id, user.id, db)

    return (project, is_owner, is_participant)


def clean_up_docs(file_keys: str) -> None:
    cleanup_db_session = db.SessionLocal()

    try:
        for file_key in file_keys:
            delete_files(file_key)
            cleanup_db_session.delete(cleanup_db_session.query(models.Document).filter(
                models.Document.file_key == file_key).first())

        cleanup_db_session.commit()

    except Exception as e:
        cleanup_db_session.rollback()
        raise

    finally:
        cleanup_db_session.close()


def get_doc_or_error(doc_id: int, db: Session) -> models.Document:
    doc: models.Document | None = db.query(models.Document).filter(
        models.Document.id == doc_id,
        models.Document.to_delete == False).first()

    if not doc:
        raise exceptions.NotFoundError("Document not found")

    return doc

def document_access_check(
        document: models.Document,
        user_id: int,
        db: Session
) -> Tuple[bool, bool]:

    full_access_allowed = document.project.owner_id == user_id
    access_as_project_participant = False
    for u in document.project.project_memberships:
        if user_id == u.user_id:
            access_as_project_participant = True
            break

    return full_access_allowed, access_as_project_participant
