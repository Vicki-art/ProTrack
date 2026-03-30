from sqlalchemy.orm import Session

from app.core import schemas
from app.database import models
from app.exceptions import exceptions
from app.database.db import db_transaction


def update_profile(
        user_id: int,
        profile_info: schemas.ProfileIn,
        current_user: models.User,
        db: Session
) -> models.Profile:

    if user_id != current_user.id:
        raise exceptions.ForbiddenActionError("You can not modify this profile")

    current_user_profile: models.Profile | None = db.query(models.Profile).filter(
        models.Profile.user_id == current_user.id
    ).first()

    if current_user_profile is None:
        raise exceptions.NotFoundError("Profile not found")

    with db_transaction(db):
        current_user_profile.first_name = profile_info.first_name
        current_user_profile.last_name = profile_info.last_name
        current_user_profile.email = profile_info.email

    db.refresh(current_user_profile)

    return current_user_profile


def show_profile(
        user_id: int,
        db: Session
) -> models.Profile:

    searched_profile: models.Profile | None = db.query(models.Profile).filter(
        models.Profile.user_id == user_id
    ).first()

    if searched_profile is None:
        raise exceptions.NotFoundError("User not found")

    return searched_profile
