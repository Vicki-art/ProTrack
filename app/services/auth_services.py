import logging

from sqlalchemy.orm import Session

from app.core import schemas, oauth2
from app.database import models
from app.exceptions import exceptions
from app.database.db import db_transaction
from app.database.db_helpers import get_user_by_username

logger = logging.getLogger(__name__)


def create_user(
        user: schemas.UserCreate,
        db: Session
) -> models.User:
    """
    Create a new user in the system.

    Checks if the username already exists, hashes the password,
    and creates a user with an empty profile.

    Args:
        user: User creation data (username and password).
        db: Database session.

    Returns:
        Created User ORM model.

    Raises:
        DataConflictError: If username already exists.
    """
    hashed_password = oauth2.hash_password(user.password)

    existing_user: models.User | None = get_user_by_username(user.username, db)

    if existing_user:
        raise exceptions.DataConflictError("Username already exists")

    with db_transaction(db):
        new_user = models.User(
            username=user.username,
            password=hashed_password,
            profile=models.Profile()
        )
        db.add(new_user)

    db.refresh(new_user)

    return new_user


def login(
        user_credentials: schemas.LoginCredentials,
        db: Session
) -> str:
    """
    Authenticate user and generate access token.

    Verifies user credentials and returns a JWT access token
    if authentication is successful.

    Args:
        user_credentials: Login credentials (login(username) and password).
        db: Database session.

    Returns:
        JWT access token as a string.

    Raises:
        InvalidCredentialsError: If username or password is incorrect.
    """
    user: models.User | None = get_user_by_username(user_credentials.login, db)

    if not user:
        raise exceptions.InvalidCredentialsError()

    if not oauth2.verify(user_credentials.password, user.password):
        raise exceptions.InvalidCredentialsError()

    access_token = oauth2.create_access_token(
        data={"user_id": str(user.id)}
    )
    return access_token
