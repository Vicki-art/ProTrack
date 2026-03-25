from app import exceptions
from app import models, utils
from sqlalchemy.exc import SQLAlchemyError
from app.helpers.db_helpers import (
    clean_up_files,
    get_project_or_error,
    get_user_or_error,
    check_membership,
    get_user_by_username_or_error
)

from app.helpers import file_helpers

def create_project(project_info, current_user, db):
    new_project = models.Project(name=project_info.name,
                                 description=project_info.description,
                                 owner_id=current_user.id
                                 )
    try:
        db.add(new_project)
        db.commit()
        db.refresh(new_project)
    except SQLAlchemyError as e:
        db.rollback()
        raise exceptions.DatabaseError(detail=str(e))

    return new_project


def get_project_info(project_id, current_user, db):
    requested_project = get_project_or_error(project_id, db)
    is_owner = current_user.id == requested_project.owner_id
    if is_owner:
        return requested_project

    is_participant = check_membership(project_id, current_user.id, db)
    if not is_participant:
        raise exceptions.ForbiddenActionError("You have no access")

    return requested_project


def modify_project(project_id, updated_fields, current_user, db):
    project_to_update = get_project_or_error(project_id, db)
    is_owner = current_user.id == project_to_update.owner_id
    is_participant = check_membership(project_id, current_user.id, db)

    if not is_owner and not is_participant:
        raise exceptions.ForbiddenActionError("You have no access")

    project_to_update.name = updated_fields.name
    project_to_update.description = updated_fields.description

    try:
        db.commit()
        db.refresh(project_to_update)
    except SQLAlchemyError as e:
        raise exceptions.DatabaseError(detail=str(e))

    return project_to_update


def add_new_participant(new_participant_username, project_id, current_user, db):
    project = get_project_or_error(project_id, db)
    is_owner = current_user.id == project.owner_id
    if not is_owner:
        raise exceptions.ForbiddenActionError("Only project owner can perform this action")

    new_participant = get_user_by_username_or_error(new_participant_username, db)

    is_current_participant = check_membership(project_id,
                                              new_participant.id,
                                              db)
    if is_current_participant:
        raise exceptions.DataConflictError("User has already been added to the project")

    new_membership = models.UserProject(project_id=project_id,
                                        user_id=new_participant.id,
                                        role=models.ProjectRole.participant)

    try:
        db.add(new_membership)
        db.commit()
        db.refresh(new_membership)
    except SQLAlchemyError as e:
        db.rollback()
        raise exceptions.DatabaseError(detail=str(e))

    return new_membership


def delete_participant(project_id, participant_username, current_user, db):
    project_to_update = get_project_or_error(project_id, db)
    is_owner = current_user.id == project_to_update.owner_id
    if not is_owner:
        raise exceptions.ForbiddenActionError("Only project owner can perform this action")

    participant_to_delete = get_user_by_username_or_error(participant_username, db)

    project_membership = check_membership(project_id, participant_to_delete.id, db)

    if not project_membership:
        raise exceptions.DataConflictError("User has no membership in the project")

    try:
        db.delete(project_membership)
        db.commit()
    except SQLAlchemyError as e:
        raise exceptions.DatabaseError(detail=str(e))

    return


def share_participation(project_id, current_user, db):
    shared_project = get_project_or_error(project_id, db)

    is_owner = shared_project.owner_id == current_user.id
    if not is_owner:
        raise exceptions.ForbiddenActionError("Only project owner can perform this action")

    project_token = utils.create_project_access_token(data={
        "owner_id": str(current_user.id),
        "project_id": str(project_id)
    })

    return project_token


def join_project_via_link(token, current_user, db):
    owner, project = utils.get_project_data_from_token(token, db)

    is_owner = project.owner_id == owner.id
    if not is_owner:
        raise exceptions.NotFoundError("Invalid access link")

    add_new_participant(current_user.username, project.id, owner, db)
    return project

def delete_project(project_id, background_tasks, current_user, db):
    project_to_delete = get_project_or_error(project_id, db)
    is_owner = project_to_delete.owner_id == current_user.id
    if not is_owner:
        raise exceptions.ForbiddenActionError("Only project owner can perform this action")

    files_to_cleanup = []

    try:
        for f in project_to_delete.project_docs:
            if not f.file.general_purpose:
                f.file.to_delete = True
                files_to_cleanup.append(f.file.file_key)
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise exceptions.DatabaseError(detail=str(e))
    except Exception as e:
        db.rollback()
        raise



    try:
        db.delete(project_to_delete)
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise exceptions.DatabaseError(detail=str(e))

    background_tasks.add_task(clean_up_files, files_to_cleanup)

    return



