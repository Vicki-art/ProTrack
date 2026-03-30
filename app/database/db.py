from typing import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.exceptions import exceptions


DATABASE_URL = (
    f"postgresql://{settings.database_username}:"
    f"{settings.database_password}@{settings.database_hostname}:"
    f"{settings.database_port}/{settings.database_name}"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def db_transaction(db: Session,
                   rollback_file_f=None,
                   rollback_files=None,
                   storage=None
) -> Generator:

    try:
        yield
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        if rollback_file_f and rollback_files:
            rollback_file_f(rollback_files, storage)
        raise exceptions.DatabaseError(detail=str(e))
    except Exception:
        db.rollback()
        if rollback_file_f and rollback_files:
            rollback_file_f(rollback_files, storage)
        raise
