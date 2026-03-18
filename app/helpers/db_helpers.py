from app import models, exceptions


def get_project_or_error(project_id, db):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise exceptions.ProjectNotFoundError()

    return project


def get_user_or_error(user_id, db):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise exceptions.UserNotFoundError()

    return user


def get_user_by_username_or_error(username, db):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise exceptions.UserNotFoundError()

    return user


def check_membership(project_id, user_id, db):
    membership = db.query(models.UserProject).filter(
        models.UserProject.user_id == user_id,
        models.UserProject.project_id == project_id

    ).first()

    return membership
