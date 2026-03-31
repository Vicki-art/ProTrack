from sqlalchemy.orm import Session

from app.core import schemas
from app.database import models
from app.exceptions import exceptions
from app.database.db import db_transaction
from app.database.db_helpers import get_profile_or_error


def update_profile(
        user_id: int,
        profile_info: schemas.ProfileIn,
        current_user: models.User,
        db: Session
) -> models.Profile:
    """
    Update the authenticated user's profile.

    Allows a user to update only their own profile.

    Args:
        user_id: ID of the profile to update.
        profile_info: New profile data.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        Updated Profile ORM object.

    Raises:
        ForbiddenActionError: If user attempts to update another user's profile.
        NotFoundError: If profile does not exist.
        """

    if user_id != current_user.id:
        raise exceptions.ForbiddenActionError("You cannot modify another user's profile")

    current_user_profile = get_profile_or_error(current_user.id, db)

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
    """
    Retrieve a user profile by user ID.

    Args:
        user_id: ID of the user whose profile is requested.
        db: Database session.

    Returns:
        Profile ORM object.

    Raises:
        NotFoundError: If profile does not exist.
        """

    searched_profile = get_profile_or_error(user_id, db)

    return searched_profile
