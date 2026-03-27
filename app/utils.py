from datetime import datetime, timedelta
from typing import Any, Dict

import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app import schemas, exceptions, models
from app.config import settings


pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes


def create_project_access_token(data: Dict[str, Any]) -> str:
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def verify_project_access_token(project_token: str) -> schemas.ProjectTokenData:

    try:
        payload: Dict[str, Any] = jwt.decode(
            project_token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        owner_id: str | None = payload.get("owner_id", None)
        project_id: str | None = payload.get("project_id", None)

        if owner_id is None or project_id is None:
            raise exceptions.NotFoundError("Invalid access link")

        project_token_data = schemas.ProjectTokenData(
            owner_id=owner_id,
            project_id=project_id
        )

    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        raise exceptions.NotFoundError("Invalid access link")

    return project_token_data


def get_project_data_from_token(token: str, db: Session
                                ) -> tuple[models.User, models.Project]:

    token_data = verify_project_access_token(token)

    owner: models.User | None = db.query(models.User).filter(
        models.User.id == token_data.owner_id
    ).first()

    project: models.User | None = db.query(models.Project).filter(
        models.Project.id == token_data.project_id
    ).first()

    if not owner or not project:
        raise exceptions.NotFoundError("Access link invalid")

    return owner, project
