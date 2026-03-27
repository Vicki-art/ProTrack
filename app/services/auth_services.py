from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import utils, models, oauth2, exceptions, schemas


def create_user(
        user: models.User,
        db: Session
) -> models.User:

    hashed_password = utils.hash_password(user.password)

    existing_user: models.User | None = db.query(models.User).filter(
        models.User.username == user.username
    ).first()

    if existing_user:
        raise exceptions.DataConflictError("Username already exists")

    new_user = models.User(
        username=user.username,
        password=hashed_password,
        profile=models.Profile()
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

    except SQLAlchemyError as e:
        db.rollback()
        raise exceptions.DatabaseError()

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

    if not utils.verify(user_credentials.password, user.password):
        raise exceptions.InvalidCredentialsError()

    access_token = oauth2.create_access_token(
        data={"user_id": str(user.id)}
    )
    return access_token
