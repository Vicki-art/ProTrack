from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core import schemas, oauth2
from app.services import users_services
from app.database.db import get_db
from app.database import models

router = APIRouter()


@router.put(
    "/{user_id}/profile",
    response_model=schemas.ProfileOut,
    status_code=status.HTTP_200_OK
)
def update_profile_info(
        user_id: int,
        profile_info: schemas.ProfileIn,
        current_user: models.User = Depends(oauth2.get_current_user),
        db: Session = Depends(get_db)
) -> schemas.ProfileOut:
    """
    Update profile info by profile owner
    """
    updated_profile = users_services.update_profile(
        user_id,
        profile_info,
        current_user,
        db
    )

    return updated_profile


@router.get(
    "/{user_id}/profile",
    name="profile",
    response_model=schemas.ProfileOut,
    status_code=status.HTTP_200_OK
)
def get_profile_info(
        user_id: int,
        current_user: models.User = Depends(oauth2.get_current_user),
        db: Session = Depends(get_db)
) -> schemas.ProfileOut:
    """
    Get profile info authenticated user
    """
    searched_profile = users_services.show_profile(user_id, db)

    return searched_profile
