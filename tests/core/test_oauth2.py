import jwt
import pytest

from app.core import oauth2
from app.exceptions import exceptions


def test_password_hash_and_verify():
    password = "Password123"

    hashed = oauth2.hash_password(password)

    assert hashed != password
    assert oauth2.verify(password, hashed) is True


def test_create_access_token():
    data = {"user_id": 1}

    token = oauth2.create_access_token(data)

    assert isinstance(token, str)
    assert token is not None


def test_verify_access_token():
    data = {"user_id": 1}

    token = oauth2.create_access_token(data)
    result = oauth2.verify_access_token(token)

    assert result.id == 1


def test_invalid_token():
    with pytest.raises(exceptions.InvalidCredentialsError):
        oauth2.verify_access_token("invalid token")


def test_token_without_user_id():
    payload = {"some": "data"}

    token = jwt.encode(
        payload,
        oauth2.SECRET_KEY,
        algorithm=oauth2.ALGORITHM
    )

    with pytest.raises(exceptions.InvalidCredentialsError):
        oauth2.verify_access_token(token)
