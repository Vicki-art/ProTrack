from app import exceptions
from app import models
from sqlalchemy.exc import SQLAlchemyError

def update_profile(user_id, profile_info, current_user, db):
    if user_id != current_user.id:
        raise exceptions.ForbiddenActionError("You can not modify this profile")

    current_user_profile = db.query(models.Profile).filter(
        models.Profile.user_id == current_user.id).first()

    if not current_user_profile:
        raise exceptions.NotFoundError("Profile not found")

    current_user_profile.first_name = profile_info.first_name
    current_user_profile.last_name = profile_info.last_name
    current_user_profile.email = profile_info.email

    try:
        db.commit()
        db.refresh(current_user_profile)
    except SQLAlchemyError as e:
        db.rollback()
        raise exceptions.DatabaseError(detail=str(e))

    return current_user_profile


def show_profile(user_id, db):
    searched_profile = db.query(models.Profile).filter(models.Profile.user_id == user_id).first()
    if not searched_profile:
        raise exceptions.NotFoundError("User not found")

    return searched_profile

