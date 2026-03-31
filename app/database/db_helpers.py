from sqlalchemy.orm import Session

from app.database import models, db
from app.exceptions import exceptions
from app.storage.base import BaseStorage


def get_project_or_error(
        project_id: int,
        db: Session
) -> models.Project:
    """
    Retrieve a project by ID.

    Raises:
        NotFoundError: if project does not exist

    Returns:
        Project instance
    """

    project: models.Project | None = db.query(models.Project).filter(
        models.Project.id == project_id
    ).first()

    if not project:
        raise exceptions.NotFoundError("Project not found")

    return project


def get_user_by_username(
        username: str,
        db: Session
) -> models.User:
    """
    Retrieve a user by username.

    Returns:
        User instance or None if not found
    """

    user: models.User | None = db.query(models.User).filter(
        models.User.username == username
    ).first()

    return user


def get_profile_or_error(
        user_id: int,
        db: Session
) -> models.Profile:
    """
    Retrieve user profile by user ID.

    Raises:
        NotFoundError: if profile does not exist

    Returns:
        Profile instance
    """
    profile: models.Profile | None = db.query(models.Profile).filter(
        models.Profile.user_id == user_id
    ).first()

    if profile is None:
        raise exceptions.NotFoundError("Profile not found")

    return profile


def get_user_by_username_or_error(
        username: str,
        db: Session
) -> models.User:
    """
    Retrieve a user by username.

    Raises:
        NotFoundError: if user does not exist

    Returns:
        User instance
    """
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
    """
    Check if user is a member of a project.

    Returns:
        UserProject instance if membership exists, otherwise None
    """

    membership: models.UserProject | None = db.query(models.UserProject).filter(
        models.UserProject.user_id == user_id,
        models.UserProject.project_id == project_id

    ).first()

    return membership


def get_doc_or_error(doc_id: int, db: Session) -> models.Document:
    """
    Retrieve a document by ID.

    Conditions:
    - Document must not be marked as deleted
    - Document must belong to a project

    Raises:
        NotFoundError: if document does not exist or is invalid

    Returns:
        Document instance
    """
    doc: models.Document | None = db.query(models.Document).filter(
        models.Document.id == doc_id,
        models.Document.to_delete == False,
        models.Document.project_id.is_not(None)
    ).first()

    if not doc:
        raise exceptions.NotFoundError("Document not found")

    return doc


def check_project_access(
    project: models.Project,
    user: models.User,
    db: Session,
    allow_participant: bool = True
) -> None:
    """
    Validate user access to a project.

    Rules:
    - Project owner has full access
    - If allow_participant=True, project members are allowed
    - Otherwise only owner is allowed

    Raises:
        ForbiddenActionError: if access is denied

    Returns:
        None
    """
    is_owner = user.id == project.owner_id

    if is_owner:
        return

    if allow_participant:
        is_participant = check_membership(project.id, user.id, db)
        if is_participant:
            return

    raise exceptions.ForbiddenActionError("Access denied")


def check_project_access_allow_only_for_owner(
    project: models.Project,
    user: models.User,
    db: Session
) -> None:
    """
    Validate that only project owner can perform action.

    Rules:
    - Owner is allowed
    - Project members are explicitly forbidden
    - Non-related users are denied

    Raises:
        ForbiddenActionError: if user is not project owner

    Returns:
        None
    """
    is_owner = user.id == project.owner_id
    membership_exists = check_membership(project.id, user.id, db)

    if is_owner:
        return

    if membership_exists:
        raise exceptions.ForbiddenActionError("Only project owner can perform this action")

    raise exceptions.ForbiddenActionError("Access denied")


def clean_up_docs(file_keys: list, storage: BaseStorage) -> None:
    """
    Cleanup deleted documents from storage and database.

    Behavior:
    - Deletes files from external storage
    - Removes corresponding DB records
    - Uses isolated DB session for safety
    - Rolls back DB changes if failure occurs

    Args:
        file_keys: list of storage file identifiers to remove
        storage: storage backend implementation

    Returns:
        None
    """
    session = db.SessionLocal()
    try:
        for file_key in file_keys:

            storage.delete_file(file_key)
            doc = session.query(models.Document).filter(
                models.Document.file_key == file_key).first()
            if doc:
                session.delete(doc)

        session.commit()

    except Exception as e:
        session.rollback()
        raise

    finally:
        session.close()
