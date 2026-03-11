from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from app import utils, models

def create_user(user, db):
    hashed_password = utils.hash(user.password)
    user.password = hashed_password

    new_user = models.User(username=user.username,
                           password=user.password, profile=models.Profile())
    db.add(new_user)

    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        constraint = getattr(e.orig.diag, "constraint_name", "")
        if constraint == "unique_username":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already exists")

        raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database error")

    db.refresh(new_user)

    return new_user