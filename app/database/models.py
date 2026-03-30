import enum

import sqlalchemy as sa
from sqlalchemy.orm import relationship
from sqlalchemy.ext.associationproxy import association_proxy

from app.database.db import Base


class User(Base):
    __tablename__ = "users"

    id = sa.Column(sa.Integer, primary_key=True)
    username = sa.Column(sa.String(50), nullable=False)
    password = sa.Column(sa.String(255), nullable=False)
    created_at = sa.Column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now()
    )

    uploaded_documents = relationship(
        "Document",
        back_populates="uploaded_by_user"
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

    projects = association_proxy(
        "project_memberships",
        "project"
    )

    __table_args__ = (
        sa.UniqueConstraint("username", name="unique_username"),
    )


class Profile(Base):
    __tablename__ = "profiles"

    id = sa.Column(sa.Integer, primary_key=True)
    first_name = sa.Column(sa.String(100))
    last_name = sa.Column(sa.String(100))
    email = sa.Column(sa.String(254), unique=True)
    user_id = sa.Column(
        sa.Integer,
        sa.ForeignKey("users.id"),
        unique=True,
        nullable=False
    )

    user = relationship(
        "User",
        back_populates="profile"
    )


class Project(Base):
    __tablename__ = "projects"

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(255))
    description = sa.Column(sa.Text)
    created_at = sa.Column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now()
    )

    owner_id = sa.Column(
        sa.Integer,
        sa.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        name="fk_projects_owner_id"
    )

    storage_used_bytes = sa.Column(
        sa.BigInteger,
        default=0,
        nullable=False
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

    docs = relationship(
        "Document",
        back_populates="project",
        foreign_keys="[Document.project_id]",
        primaryjoin="and_(Project.id==Document.project_id, Document.to_delete==False)",
        lazy="selectin"
    )

    users = association_proxy(
        "project_memberships",
        "user"
    )


class ProjectRole(enum.Enum):
    participant = "participant"


class UserProject(Base):
    __tablename__ = "users_projects"

    user_id = sa.Column(
        sa.Integer,
        sa.ForeignKey("users.id"),
        primary_key=True,
        nullable=False)
    project_id = sa.Column(
        sa.Integer,
        sa.ForeignKey("projects.id"),
        primary_key=True,
        nullable=False)
    role = sa.Column(
        sa.Enum(ProjectRole, name="projectrole", create_type=False),
        nullable=False)

    user = relationship(
        "User",
        back_populates="project_memberships"
    )

    project = relationship(
        "Project",
        back_populates="project_memberships"
    )


class Document(Base):
    __tablename__ = "documents"

    id = sa.Column(sa.Integer, primary_key=True, nullable=False)
    original_filename = sa.Column(sa.String, nullable=False)
    file_key = sa.Column(sa.String, unique=True, nullable=False)
    size = sa.Column(sa.BigInteger, nullable=False)
    content_type = sa.Column(sa.String, nullable=False)
    project_id = sa.Column(sa.Integer, sa.ForeignKey("projects.id"), nullable=True, index=True)
    to_delete = sa.Column(sa.Boolean, default=False, index=True)
    uploaded_by = sa.Column(sa.Integer, sa.ForeignKey("users.id"), nullable=False)
    uploaded_at = sa.Column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now()
    )

    project = relationship(
        "Project",
        back_populates="docs"
    )

    uploaded_by_user = relationship(
        "User",
        foreign_keys=[uploaded_by],
        back_populates="uploaded_documents"
    )
