from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app import schemas
from app.services import auth_services


router = APIRouter()


@router.post(
    "/auth",
    status_code=status.HTTP_201_CREATED
)
def sign_up(
        user: schemas.UserCreate,
        request: Request,
        db: Session = Depends(get_db)
) -> dict:

    new_user = auth_services.create_user(user, db)
    profile_url = request.url_for("profile", user_id=new_user.id)

    return {
        "message": "User account was successfully created",
        "user_id": new_user.id,
        "username": new_user.username,
        "first name": getattr(new_user.profile, "first_name", "N/A"),
        "last name": getattr(new_user.profile, "last_name", "N/A"),
        "email": getattr(new_user.profile, "email", "N/A"),
        "profile_link": str(profile_url)
        }


@router.post(
    '/login',
    response_model=schemas.Token
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
