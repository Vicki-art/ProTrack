from app import models, exceptions, db
from app.helpers.file_helpers import delete_files


def get_project_or_error(project_id, db):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise exceptions.NotFoundError("Project not found")

    return project


def get_user_or_error(user_id, db):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise exceptions.NotFoundError("User not found")

    return user


def get_user_by_username_or_error(username, db):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise exceptions.NotFoundError("User not found")

    return user


def check_membership(project_id, user_id, db):
    membership = db.query(models.UserProject).filter(
        models.UserProject.user_id == user_id,
        models.UserProject.project_id == project_id

    ).first()

    return membership

def project_and_user_status(project_id, user, db):
    project = get_project_or_error(project_id, db)
    is_owner = user.id == project.owner_id
    is_participant = check_membership(project_id, user.id, db)
    return (project, is_owner, is_participant)


def clean_up_files(file_keys):
    cleanup_db_session = db.SessionLocal()

    try:
        files = cleanup_db_session.query(models.File).filter(
        models.File.file_key.in_(file_keys)).all()

        for file in files:
            delete_files([file.file_key])
            cleanup_db_session.delete(file)

        cleanup_db_session.commit()

    except Exception as e:
        cleanup_db_session.rollback()
        raise

    finally:
        cleanup_db_session.close()

def get_doc_or_error(doc_id, db):
    doc = db.query(models.File).filter(models.File.id == doc_id).first()
    if not doc:
        raise exceptions.NotFoundError("Document not found")
    return doc
