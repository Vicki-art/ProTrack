from fastapi import APIRouter, Depends, status
from app import oauth2, schemas
from sqlalchemy.orm import Session
from app.services import users_services
from app.db import get_db

router = APIRouter()


@router.put("/{user_id}/profile", response_model=schemas.ProfileOut, status_code=status.HTTP_200_OK)
def update_profile_info(
        user_id: int,
        profile_info: schemas.ProfileIn,
        current_user = Depends(oauth2.get_current_user),
        db: Session = Depends(get_db)):
    updated_profile = users_services.update_profile(user_id,
                                                    profile_info,
                                                    current_user,
                                                    db)
    return updated_profile


@router.get("/{user_id}/profile", response_model=schemas.ProfileOut, status_code=status.HTTP_200_OK)
def get_profile_info(
        user_id: int,
        current_user = Depends(oauth2.get_current_user),
        db: Session = Depends(get_db)):
    searched_profile = users_services.show_profile(user_id, db)
    return searched_profile