from typing import List

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app import exceptions, models, utils, schemas
from app.helpers.db_helpers import (
    clean_up_docs,
    get_project_or_error,
    check_membership,
    get_user_by_username_or_error
)


def create_project(
        project_info: schemas.ProjectIn,
        current_user: models.User,
        db: Session
) -> models.Project:

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


def get_project_info(
        project_id: int,
        current_user: models.User,
        db: Session
) -> models.Project:

    requested_project = get_project_or_error(project_id, db)
    is_owner = current_user.id == requested_project.owner_id

    if is_owner:
        return requested_project

    is_participant = check_membership(project_id, current_user.id, db)

    if not is_participant:
        raise exceptions.ForbiddenActionError("You have no access")

    return requested_project


def modify_project(
        project_id: int,
        updated_fields: schemas.ProjectIn,
        current_user: models.User,
        db: Session
) -> models.Project:

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


def add_new_participant(
        new_participant_username: str,
        project_id: int,
        current_user: models.User,
        db: Session
) -> models.UserProject:
    project = get_project_or_error(project_id, db)
    is_owner = current_user.id == project.owner_id

    if not is_owner:
        raise exceptions.ForbiddenActionError("Only project owner can perform this action")

    if new_participant_username == current_user.username:
        raise exceptions.DataConflictError("Owner has already participated in the project")

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


def delete_participant(
        project_id: int,
        participant_username: str,
        current_user: models.User,
        db: Session
) -> None:

    project_to_update = get_project_or_error(project_id, db)
    is_owner = current_user.id == project_to_update.owner_id

    if not is_owner:
        raise exceptions.ForbiddenActionError(
            "Only project owner can perform this action"
        )

    if participant_username == current_user.username:
        raise exceptions.DataConflictError(
            "Can not delete project owner from the list of participants"
        )

    participant_to_delete = get_user_by_username_or_error(participant_username, db)

    project_membership = check_membership(project_id, participant_to_delete.id, db)

    if not project_membership:
        raise exceptions.DataConflictError(
            "User has no membership in the project"
        )

    try:
        db.delete(project_membership)
        db.commit()
    except SQLAlchemyError as e:
        raise exceptions.DatabaseError(detail=str(e))

    return


def share_participation(
        project_id: int,
        current_user: models.User,
        db: Session
) -> str:

    shared_project = get_project_or_error(project_id, db)

    is_owner = shared_project.owner_id == current_user.id

    if not is_owner:
        raise exceptions.ForbiddenActionError(
            "Only project owner can perform this action"
        )

    project_token = utils.create_project_access_token(data={
        "owner_id": str(current_user.id),
        "project_id": str(project_id)
    })

    return project_token


def join_project_via_link(
        token: str,
        current_user: models.User,
        db: Session
) -> models.Project:
    owner, project = utils.get_project_data_from_token(token, db)

    is_owner = project.owner_id == owner.id
    if not is_owner:
        raise exceptions.NotFoundError("Invalid access link")

    add_new_participant(current_user.username, project.id, owner, db)

    return project


def delete_project(
        project_id: int,
        background_tasks: BackgroundTasks,
        current_user: models.User,
        db: Session
) -> None:

    project_to_delete = get_project_or_error(project_id, db)
    is_owner = project_to_delete.owner_id == current_user.id

    if not is_owner:
        raise exceptions.ForbiddenActionError(
            "Only project owner can perform this action"
        )

    files_to_cleanup: List[str] = []

    try:
        for doc in project_to_delete.docs:
            doc.to_delete = True
            doc.project_id = None
            files_to_cleanup.append(doc.file_key)
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
    print(files_to_cleanup)
    background_tasks.add_task(clean_up_docs, files_to_cleanup)

    return
