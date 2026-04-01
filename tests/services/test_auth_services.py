import pytest
from unittest.mock import Mock

from app.services.auth_services import create_user, login
from app.core import schemas
from app.database import models
from app.exceptions import exceptions


def test_create_user_success(mocker):
    db = Mock()

    user_input = schemas.UserCreate(
        login="test_user",
        password="Password123",
        repeat_password="Password123"
    )

    mocker.patch(
        "app.services.auth_services.get_user_by_username",
        return_value=None
    )

    mocker.patch(
        "app.services.auth_services.oauth2.hash_password",
        return_value="hashed_password"
    )

    mocker.patch(
        "app.services.auth_services.db_transaction"
    ).return_value.__enter__ = Mock()

    user = create_user(user_input, db)

    assert user.username == "test_user"
    assert user.password == "hashed_password"


def test_create_user_user_exists(mocker):
    db = Mock()

    user_input = schemas.UserCreate(
        login="test_user",
        password="Password123",
        repeat_password = "Password123"
    )

    mocker.patch(
        "app.services.auth_services.get_user_by_username",
        return_value=models.User()
    )

    with pytest.raises(exceptions.DataConflictError):
        create_user(user_input, db)

def test_create_user_calls_hash_password(mocker):
    db = Mock()

    user_input = schemas.UserCreate(
        login="test_user",
        password="Password123",
        repeat_password="Password123"
    )

    mock_hash = mocker.patch(
        "app.services.auth_services.oauth2.hash_password",
        return_value="hashed"
    )

    mocker.patch(
        "app.services.auth_services.get_user_by_username",
        return_value=None
    )

    mocker.patch(
        "app.services.auth_services.db_transaction"
    ).return_value.__enter__ = Mock()

    create_user(user_input, db)

    mock_hash.assert_called_once_with("Password123")

def test_login_success(mocker):
    db = Mock()

    user = Mock()
    user.password = "hashed_password"
    user.username = "test_user"

    mocker.patch(
        "app.services.auth_services.get_user_by_username",
        return_value=user
    )

    mocker.patch(
        "app.core.oauth2.verify",
        return_value=True
    )

    mock_create_token = mocker.patch(
        "app.services.auth_services.oauth2.create_access_token",
        return_value="fake_jwt"
    )

    user_credentials = schemas.LoginCredentials(
        login="test_user",
        password="Password123"
    )

    result = login(user_credentials, db)

    assert result == "fake_jwt"
    mock_create_token.assert_called_once()


def test_login_user_not_found(mocker):
    db = Mock()

    mocker.patch(
        "app.services.auth_services.get_user_by_username",
        return_value=None
    )

    user_credentials = schemas.LoginCredentials(
        login="test_user",
        password="Password123"
    )

    with pytest.raises(exceptions.InvalidCredentialsError):
        login(user_credentials, db)


def test_login_wrong_password(mocker):
    db = Mock()

    user = Mock()
    user.password = "hashed_password"

    mocker.patch(
        "app.services.auth_services.get_user_by_username",
        return_value=user
    )

    mocker.patch(
        "app.core.oauth2.verify",
        return_value=False
    )

    user_credentials = schemas.LoginCredentials(
        login="test_user",
        password="Password123"
    )

    with pytest.raises(exceptions.InvalidCredentialsError):
        login(user_credentials, db)