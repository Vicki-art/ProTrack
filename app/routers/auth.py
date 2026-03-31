from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.core import schemas
from app.services import auth_services


router = APIRouter()


@router.post(
    "/register",
    response_model=schemas.UserCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Creates a new user account and returns user details."
)
def sign_up(
        user: schemas.UserCreate,
        db: Session = Depends(get_db)
) -> schemas.UserCreatedResponse:

    new_user = auth_services.create_user(user, db)

    return schemas.UserCreatedResponse(
        message="User account was successfully created.",
        user_id=new_user.id,
        username=new_user.username,
        first_name=new_user.profile.first_name,
        last_name=new_user.profile.last_name,
        email=new_user.profile.email
    )


@router.post(
    '/login',
    response_model=schemas.Token,
    summary="Authenticate user",
    description="Logs in a user and returns a JWT access token."
)
def login(
        user_credentials: schemas.LoginCredentials,
        db: Session = Depends(get_db)
) -> schemas.Token:

    access_token = auth_services.login(user_credentials, db)

    return schemas.Token(
        access_token=access_token,
        token_type="bearer"
    )
