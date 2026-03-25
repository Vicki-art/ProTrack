from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, BigInteger, Boolean, DateTime, ForeignKey, UniqueConstraint, Text, Enum, func
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
    added_documents = relationship(
        "ProjectDocument",
        back_populates="added_by_user"
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
        foreign_keys="[Project.owner_id]",
        back_populates="owner"
    )

    created_docs = relationship(
        "File",
        foreign_keys="[File.uploaded_by]",
        back_populates="creator"
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

    owner_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        name="fk_projects_owner_id"
    )

    owner = relationship(
        "User",
        foreign_keys="[Project.owner_id]",
        back_populates="owned_projects"
    )

    project_memberships = relationship(
        "UserProject",
        back_populates="project",
        cascade="all, delete-orphan"
    )

    project_docs = relationship(
        "ProjectDocument",
        back_populates="project",
        foreign_keys="[ProjectDocument.project_id]",
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

class ProjectDocument(Base):
    __tablename__ = "project_documents"

    id = Column(Integer, primary_key=True, nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    added_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    added_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )


    project = relationship(
        "Project",
        back_populates="project_docs"
    )

    file = relationship(
        "File",
        back_populates="project_links",
    )


    added_by_user = relationship(
        "User",
        foreign_keys=[added_by],
        back_populates="added_documents"
    )

    __table_args__ = (
        UniqueConstraint("project_id", "file_id", name="uq_project_file"),
    )



class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, nullable=False)
    original_filename = Column(String, nullable=False)
    file_key = Column(String, unique=True, nullable=False)
    size = Column(BigInteger, nullable=False)
    content_type = Column(String, nullable=False)
    general_purpose = Column(Boolean, default=True)
    to_delete = Column(Boolean, default=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    creator = relationship(
        "User",
        foreign_keys=[uploaded_by],
        back_populates="created_docs"
    )


    project_links = relationship(
        "ProjectDocument",
        back_populates="file",
        cascade="all, delete-orphan"
    )









