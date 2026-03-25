import jwt
from datetime import datetime, timedelta
from . import schemas, db, models
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .config import settings
from app import exceptions

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes


def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def verify_access_token(token: str) -> schemas.TokenData:

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        id: str = payload.get("user_id", None)
        if id is None:
            raise exceptions.InvalidCredentialsError("Invalid token. You need to login again")
        token_data = schemas.TokenData(id=id)
    except jwt.ExpiredSignatureError:
        raise exceptions.InvalidCredentialsError("Token expired. You need to login again")

    except jwt.InvalidTokenError:
        raise exceptions.InvalidCredentialsError("Invalid token. You need to login again")

    return token_data


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(db.get_db)):

    token_data = verify_access_token(token)

    user = db.query(models.User).filter(models.User.id == token_data.id).first()

    if not user:
        raise exceptions.InvalidCredentialsError()

    return user


