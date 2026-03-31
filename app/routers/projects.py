from typing import List

import pydantic
from fastapi import APIRouter, Depends, status, Query, Request, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from urllib.parse import urlencode

from app.core import schemas, oauth2, mapper
from app.database import models
from app.services import projects_services, documents_services
from app.database.db import get_db
from app.storage.factory import get_storage
from app.storage.base import BaseStorage

router = APIRouter()


@router.post(
    "/",
    response_model=schemas.ProjectOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create project",
    description="Create a new project owned by the authenticated user."
)
def create_project(
        project_info: schemas.ProjectIn,
        current_user: models.User = Depends(oauth2.get_current_user),
        db: Session = Depends(get_db)
) -> schemas.ProjectOut:

    created_project = projects_services.create_project(
        project_info,
        current_user,
        db
    )

    return mapper.to_project_out(created_project)


@router.get(
    "/join",
    name="join_project",
    summary="Join project via token",
    description="Add the authenticated user to a project using a share token."
)
def join_project(
    token: str = Query(..., description="Project share token"),
    current_user: models.User = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
) -> dict[str, str]:

    project = projects_services.join_project_via_link(
        token,
        current_user,
        db
    )

    return {"message": f"You became a participant of a project: {project.name}"}


@router.get(
    "/{project_id}",
    response_model=schemas.ProjectOut,
    status_code=status.HTTP_200_OK,
    summary="Get project details",
    description="Retrieve project information by ID."
)
def get_project(
        project_id: int,
        current_user: models.User = Depends(oauth2.get_current_user),
        db: Session = Depends(get_db)
) -> schemas.ProjectOut:

    requested_project = projects_services.get_project_info(
        project_id,
        current_user,
        db
    )

    return mapper.to_project_out(requested_project)


@router.put(
    "/{project_id}",
    response_model=schemas.ProjectOut,
    status_code=status.HTTP_200_OK,
    summary="Update project",
    description="""Update project name and description. 
    Requires owner or participant access."""
)
def update_project(
        project_id: int,
        updated_fields: schemas.ProjectIn,
        current_user: models.User = Depends(oauth2.get_current_user),
        db: Session = Depends(get_db)
) -> schemas.ProjectOut:

    updated_project = projects_services.modify_project(
        project_id,
        updated_fields,
        current_user,
        db
    )

    return mapper.to_project_out(updated_project)


@router.post(
    "/{project_id}/invite",
    response_model=schemas.MessageResponse,
    summary="Add project participant",
    description="Invite a user to the project by username."
)
def add_project_participant(
    project_id: int,
    username: str = Query(..., description="Login of the user to invite"),
    current_user: models.User = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
) -> schemas.MessageResponse:

    projects_services.add_new_participant(
        username,
        project_id,
        current_user,
        db
    )

    return schemas.MessageResponse(
        message="New participant was successfully added"
    )


@router.delete(
    "/{project_id}/exclude",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove project participant",
    description="Remove a participant from the project."
)
def exclude_project_participant(
        project_id: int,
        username: str = Query(..., description="Username of the user to exclude"),
        current_user: models.User = Depends(oauth2.get_current_user),
        db: Session = Depends(get_db)
) -> None:

    projects_services.delete_participant(project_id, username, current_user, db)


@router.get(
    "/{project_id}/share",
    response_model=schemas.ShareLinkResponse,
    summary="Generate share link",
    description="Generate a shareable link to join the project via token."
)
def share_project(
    request: Request,
    project_id: int,
    email: pydantic.EmailStr = Query(..., description="Email of the user to invite", alias="with"),
    current_user: models.User = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
) -> schemas.ShareLinkResponse:

    token = projects_services.share_participation(
        project_id,
        current_user,
        db
    )
    base_url = request.url_for("join_project")
    share_url = f"{base_url}?{urlencode({'token': token})}"

    return schemas.ShareLinkResponse(
        message=f"Invitation link generated and sent to email:{email}",
        share_link=share_url)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete project",
    description="Delete a project and all associated documents."
)
async def delete_project(
    project_id: int,
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
) -> None:

    projects_services.delete_project(project_id, background_tasks, current_user, db)


@router.post(
    "/{project_id}/documents",
    response_model=schemas.UploadDocsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload project documents",
    description="Upload one or more documents to the project."
)
async def upload_project_documents(
    project_id: int,
    documents: List[UploadFile] = File(...),
    current_user: models.User = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db),
    storage: BaseStorage = Depends(get_storage)
) -> schemas.UploadDocsResponse:

    project_docs = documents_services.upload_project_related_docs(
        project_id,
        documents,
        current_user,
        db,
        storage
    )

    return schemas.UploadDocsResponse(
        uploaded_documents=project_docs
    )


@router.get(
    "/{project_id}/documents",
    response_model=list[schemas.FilesOut],
    status_code=status.HTTP_200_OK,
    summary="Get project documents",
    description="Retrieve all documents associated with the project."
)
def get_project_documents(
    project_id: int,
    current_user: models.User = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
) -> list[schemas.FilesOut]:

    project_docs = documents_services.get_project_related_docs(project_id, current_user, db)

    return project_docs
