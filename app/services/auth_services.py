from app import utils, models, oauth2
from sqlalchemy.exc import SQLAlchemyError
from app import exceptions


def create_user(user, db):
    hashed_password = utils.hash(user.password)

    new_user = models.User(username=user.username,
                           password=hashed_password, profile=models.Profile())

    existing_user = db.query(models.User)\
        .filter(models.User.username == user.username)\
        .first()
    if existing_user:
        raise exceptions.DataConflictError("Username already exists")

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

    except SQLAlchemyError as e:
        db.rollback()
        raise exceptions.DatabaseError(detail=str(e))

    return new_user


def login(user_credentials, db):
    user = db.query(models.User).filter(
        models.User.username == user_credentials.login).first()

    if not user:
        raise exceptions.InvalidCredentialsError()

    if not utils.verify(user_credentials.password, user.password):
        raise exceptions.InvalidCredentialsError()

    access_token = oauth2.create_access_token(data={"user_id": str(user.id)})
    return access_token
