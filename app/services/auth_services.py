from sqlalchemy.orm import Session

from app.core import schemas, oauth2
from app.database import models
from app.exceptions import exceptions
from app.database.db import db_transaction


def create_user(
        user: models.User,
        db: Session
) -> models.User:

    hashed_password = oauth2.hash_password(user.password)

    existing_user: models.User | None = db.query(models.User).filter(
        models.User.username == user.username
    ).first()

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
    user: models.User | None = db.query(models.User).filter(
        models.User.username == user_credentials.login
    ).first()

    if not user:
        raise exceptions.InvalidCredentialsError()

    if not oauth2.verify(user_credentials.password, user.password):
        raise exceptions.InvalidCredentialsError()

    access_token = oauth2.create_access_token(
        data={"user_id": str(user.id)}
    )
    return access_token
