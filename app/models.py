from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, Text, Enum, func
from sqlalchemy.ext.associationproxy import association_proxy
from app.db import Base
import enum

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False)
    password = Column(String(255), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    profile = relationship(
        "Profile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    project_memberships = relationship(
        "UserProject",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    owned_projects = relationship(
        "Project",
        back_populates="owner"
    )

    projects = association_proxy(
        "project_memberships",
        "project"
    )

    __table_args__ = (UniqueConstraint("username", name="unique_username"),)

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    email = Column(String(254), unique=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        unique=True,
        nullable=False
    )

    user = relationship(
        "User",
        back_populates="profile"
    )


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    description = Column(Text)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default= func.now(),
        onupdate=func.now()
    )

    owner_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        name="fk_projects_owner_id"
    )

    owner = relationship(
        "User",
        back_populates="owned_projects"
    )

    project_memberships = relationship(
        "UserProject",
        back_populates="project",
        cascade="all, delete-orphan"
    )

    users = association_proxy(
        "project_memberships",
        "user"
    )

class ProjectRole(enum.Enum):
    participant = "participant"


class UserProject(Base):
    __tablename__ = "users_projects"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True, nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), primary_key=True, nullable=False)
    role = Column(Enum(ProjectRole, name="projectrole", create_type=False), nullable=False)

    user = relationship(
        "User",
        back_populates="project_memberships"
    )

    project = relationship(
        "Project",
        back_populates="project_memberships"
    )












