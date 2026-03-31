from typing import Dict, Any
from datetime import datetime, timedelta

import jwt
from passlib.context import CryptContext
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core import schemas
from app.database import models
from app.exceptions import exceptions
from app.core.config import settings
from app.database.db import get_db


oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/login')

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a plain password using Argon2 algorithm.

    Returns:
        Secure hashed password string
    """
    return pwd_context.hash(password)


def verify(plain_password: str, hashed_password: str) -> bool:
    """
   Verify plain password against a hashed password.

   Returns:
       True if password matches, otherwise False
   """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: Dict[str, Any]) -> str:
    """
    Create JWT access token with expiration.

    Adds:
    - 'exp' claim with expiration time

    Args:
        data: payload dictionary (must include user identifier)

    Returns:
        Encoded JWT access token string
    """
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def verify_access_token(token: str) -> schemas.TokenData:
    """
    Decode and validate JWT access token.

    Validates:
    - Token signature
    - Token expiration
    - Presence of user_id in payload

    Raises:
        InvalidCredentialsError:
            - if token is expired
            - if token is invalid
            - if user_id is missing

    Returns:
        TokenData containing authenticated user ID
    """

    try:
        payload: Dict[str, Any] = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int | None = payload.get("user_id", None)

        if user_id is None:
            raise exceptions.InvalidCredentialsError(
                "Invalid token. You need to login again"
            )

        token_data = schemas.TokenData(id=user_id)

    except jwt.ExpiredSignatureError:
        raise exceptions.InvalidCredentialsError(
            "Token expired. You need to login again"
        )

    except jwt.InvalidTokenError:
        raise exceptions.InvalidCredentialsError(
            "Invalid token. You need to login again"
        )

    return token_data


def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
) -> models.User:
    """
    Retrieve authenticated user from JWT token.

    Steps:
    - Decode and validate JWT token
    - Extract user_id from token
    - Fetch user from database

    Raises:
        InvalidCredentialsError:
            - if token is invalid or expired
            - if user does not exist

    Returns:
        Authenticated User instance
    """

    token_data = verify_access_token(token)

    user: models.User | None = db.query(models.User).filter(
        models.User.id == token_data.id
    ).first()

    if not user:
        raise exceptions.InvalidCredentialsError()

    return user
