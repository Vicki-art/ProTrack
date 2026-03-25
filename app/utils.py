from passlib.context import CryptContext
from datetime import datetime, timedelta
from fastapi import Depends
from sqlalchemy.orm import Session
from .config import settings
from app import schemas, exceptions
import jwt
from app import db, models

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash(password: str):
    return pwd_context.hash(password)


def verify(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes


def create_project_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def verify_project_access_token(project_token: str) -> schemas.ProjectTokenData:

    try:
        payload = jwt.decode(project_token, SECRET_KEY, algorithms=[ALGORITHM])
        owner_id: str = payload.get("owner_id", None)
        project_id: str = payload.get("project_id", None)
        if owner_id is None or project_id is None:
            print("here")
            raise exceptions.NotFoundError("Invalid access link")
        project_token_data = schemas.ProjectTokenData(owner_id=owner_id, project_id=project_id)
    except jwt.ExpiredSignatureError:
        raise exceptions.TokenExpiredError()

    except jwt.InvalidTokenError:
        raise exceptions.NotFoundError("Invalid access link")

    return project_token_data


def get_project_data_from_token(token: str, db: Session):

    token_data = verify_project_access_token(token)

    owner = db.query(models.User).filter(
        models.User.id == token_data.owner_id).first()
    project = db.query(models.Project).filter(
        models.Project.id == token_data.project_id).first()

    if not owner or not project:
        raise exceptions.NotFoundError("Access link invalid")

    return owner, project
