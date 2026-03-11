from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session
from app.db import get_db
from app import schemas
from app.services import auth_services


router = APIRouter()


@router.post("/auth", status_code=status.HTTP_201_CREATED)
def sign_up(user: schemas.UserCreate, request: Request, db: Session = Depends(get_db)):
    new_user = auth_services.create_user(user, db)
    profile_url = request.url_for("profile", user_id=new_user.id)
    return {
        "message": "User account was succssfuly created",
        "user_id": new_user.id,
        "username": new_user.username,
        "name": getattr(new_user.profile, "name", "N/A"),
        "surname": getattr(new_user.profile, "surname", "N/A"),
        "email": getattr(new_user.profile, "email", "N/A"),
        "profile_link": str(profile_url)
        }


@router.post("/users/{user_id}/profile", status_code=status.HTTP_201_CREATED)
def profile(request: Request, db: Session = Depends(get_db)):
    pass
