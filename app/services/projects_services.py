from typing import List

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.core import schemas, utils
from app.database import models
from app.database.db import db_transaction
from app.exceptions import exceptions
from app.storage.factory import get_storage
from app.database.db_helpers import (
    clean_up_docs,
    get_project_or_error,
    check_membership,
    get_user_by_username_or_error,
    check_project_access,
    check_project_access_allow_only_for_owner
)


def create_project(
        project_info: schemas.ProjectIn,
        current_user: models.User,
        db: Session
) -> models.Project:
    """
    Create a new project owned by the authenticated user.

    Args:
        project_info: Project input data.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        Created Project ORM object.
    """

    with db_transaction(db):
        new_project = models.Project(name=project_info.name,
                                     description=project_info.description,
                                     owner_id=current_user.id
                                     )
        db.add(new_project)

    db.refresh(new_project)

    return new_project


def get_project_info(
        project_id: int,
        current_user: models.User,
        db: Session
) -> models.Project:
    """
    Retrieve project details if the user has access.

    Args:
        project_id: Project identifier.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        Project ORM object.

    Raises:
        ForbiddenActionError: If access is denied.
        NotFoundError: If project does not exist.
    """

    requested_project = get_project_or_error(project_id, db)
    check_project_access(requested_project, current_user, db, allow_participant=True)

    return requested_project


def modify_project(
        project_id: int,
        updated_fields: schemas.ProjectIn,
        current_user: models.User,
        db: Session
) -> models.Project:
    """
    Update project name and description.

    Args:
        project_id: Project identifier.
        updated_fields: New project data.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        Updated Project ORM object.

    Raises:
        ForbiddenActionError: If access is denied.
        NotFoundError: If project does not exist.
    """

    project_to_update = get_project_or_error(project_id, db)
    check_project_access(project_to_update, current_user, db, allow_participant=True)

    with db_transaction(db):
        project_to_update.name = updated_fields.name
        project_to_update.description = updated_fields.description

    db.refresh(project_to_update)
    return project_to_update


def add_new_participant(
        new_participant_username: str,
        project_id: int,
        current_user: models.User,
        db: Session
) -> models.UserProject:
    """
    Add a new participant to the project by username.

    Args:
        new_participant_username: Username of the user to add.
        project_id: Project identifier.
        current_user: Authenticated user (must be owner).
        db: Database session.

    Returns:
        Created UserProject association.

    Raises:
        ForbiddenActionError: If user is not the project owner.
        DataConflictError: If user is already a participant or invalid action.
        NotFoundError: If user or project does not exist.
    """
    project = get_project_or_error(project_id, db)
    print(current_user.id)
    print("I am checking")
    check_project_access_allow_only_for_owner(project, current_user, db)

    if new_participant_username == current_user.username:
        raise exceptions.DataConflictError("Owner is already a project member")

    new_participant = get_user_by_username_or_error(new_participant_username, db)

    is_current_participant = check_membership(project_id,
                                              new_participant.id,
                                              db)
    if is_current_participant:
        raise exceptions.DataConflictError("User has already been added to the project")

    with db_transaction(db):
        new_membership = models.UserProject(
            project_id=project_id,
            user_id=new_participant.id,
            role=models.ProjectRole.participant
        )
        db.add(new_membership)
    db.refresh(new_membership)

    return new_membership


def delete_participant(
        project_id: int,
        participant_username: str,
        current_user: models.User,
        db: Session
) -> None:
    """
    Remove a participant from the project.

    Args:
        project_id: Project identifier.
        participant_username: Username of the user to remove.
        current_user: Authenticated user (must be owner).
        db: Database session.

    Raises:
        ForbiddenActionError: If user is not the project owner.
        DataConflictError: If user is not a participant or invalid action.
        NotFoundError: If user or project does not exist.
    """
    project = get_project_or_error(project_id, db)
    check_project_access_allow_only_for_owner(project, current_user, db)

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

    with db_transaction(db):
        db.delete(project_membership)


def share_participation(
        project_id: int,
        current_user: models.User,
        db: Session
) -> str:
    """
    Generate a share token for project participation.

    Args:
        project_id: Project identifier.
        current_user: Authenticated user (must be owner).
        db: Database session.

    Returns:
        Share token string.

    Raises:
        ForbiddenActionError: If user is not the project owner.
        NotFoundError: If project does not exist.
    """

    shared_project = get_project_or_error(project_id, db)

    check_project_access_allow_only_for_owner(shared_project, current_user, db)

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
    """
    Join a project using a share token.

    Args:
        token: Share token.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        Project ORM object.

    Raises:
        NotFoundError: If token is invalid.
        DataConflictError: If user is already a participant.
    """
    owner, project = utils.get_project_data_from_token(token, db)

    if project.owner_id != owner.id:
        raise exceptions.NotFoundError("Invalid access link")

    if current_user.id == owner.id:
        raise exceptions.DataConflictError(
            "Owner is already a project member"
        )

    membership_exists = check_membership(project.id, current_user.id, db)
    if membership_exists:
        raise exceptions.DataConflictError(
            "User is already a project participant"
        )

    with db_transaction(db):
        membership = models.UserProject(
            project_id=project.id,
            user_id=current_user.id,
            role=models.ProjectRole.participant
        )
        db.add(membership)

    return project


def delete_project(
        project_id: int,
        background_tasks: BackgroundTasks,
        current_user: models.User,
        db: Session
) -> None:
    """
    Delete a project and schedule cleanup of related files.

    Args:
        project_id: Project identifier.
        background_tasks: FastAPI background tasks manager.
        current_user: Authenticated user (must be owner).
        db: Database session.

    Raises:
        ForbiddenActionError: If user is not the project owner.
        NotFoundError: If project does not exist.
    """

    project_to_delete = get_project_or_error(project_id, db)
    check_project_access_allow_only_for_owner(project_to_delete, current_user, db)

    files_to_cleanup: List[str] = []

    with db_transaction(db):
        for doc in project_to_delete.docs:
            doc.to_delete = True
            doc.project_id = None
            files_to_cleanup.append(doc.file_key)

        db.delete(project_to_delete)

    background_tasks.add_task(clean_up_docs, files_to_cleanup, storage=get_storage())
