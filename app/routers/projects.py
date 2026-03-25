import pydantic
from fastapi import APIRouter, Depends, status, Query, Request, UploadFile, File, BackgroundTasks
from app import oauth2, schemas
from sqlalchemy.orm import Session
from app.services import projects_services, documents_services
from urllib.parse import urlencode
from typing import List
from app.db import get_db

router = APIRouter()


@router.post("/", response_model=schemas.ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
        project_info: schemas.ProjectIn,
        current_user = Depends(oauth2.get_current_user),
        db: Session = Depends(get_db)
):
    created_project = projects_services.create_project(project_info, current_user, db)

    return schemas.ProjectOut(
        id=created_project.id,
        name=created_project.name,
        description=created_project.description,
        owner=schemas.ProfileOut(
            first_name= created_project.owner.profile.first_name,
            last_name=created_project.owner.profile.last_name,
            email=created_project.owner.profile.email
        ))


@router.get("/join", name="join_project")
def join_project(
    token: str = Query(..., description="Share token"),
    current_user = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
):
    project = projects_services.join_project_via_link(token, current_user, db)

    return {"message": f"You became a participant of a project: {project.name}"}


@router.get("/{project_id}", response_model=schemas.ProjectOut, status_code=status.HTTP_200_OK)
def get_project(
        project_id: int,
        current_user = Depends(oauth2.get_current_user),
        db: Session = Depends(get_db)
):
    requested_project = projects_services.get_project_info(project_id, current_user, db)

    return schemas.ProjectOut(
        id=requested_project.id,
        name=requested_project.name,
        description=requested_project.description,
        owner=schemas.ProfileOut(
            first_name= requested_project.owner.profile.first_name,
            last_name=requested_project.owner.profile.last_name,
            email=requested_project.owner.profile.email
        ))


@router.put("/{project_id}", response_model=schemas.ProjectOut, status_code=status.HTTP_200_OK)
def update_project(
        project_id: int,
        updated_fields: schemas.ProjectIn,
        current_user = Depends(oauth2.get_current_user),
        db: Session = Depends(get_db)
):
    updated_project = projects_services.modify_project(
        project_id,
        updated_fields,
        current_user,
        db)

    return schemas.ProjectOut(
        id=updated_project.id,
        name=updated_project.name,
        description=updated_project.description,
        owner=schemas.ProfileOut(
            first_name= updated_project.owner.profile.first_name,
            last_name=updated_project.owner.profile.last_name,
            email=updated_project.owner.profile.email
        ))


@router.post("/{project_id}/invite")
def add_project_participant(
    project_id: int,
    user: str = Query(..., description="Login of the user to invite"),
    current_user = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
):
    projects_services.add_new_participant(
        user,
        project_id,
        current_user,
        db
    )

    return {"message": "New participant was successfully added"}


@router.delete("/{project_id}/exclude", status_code=status.HTTP_204_NO_CONTENT)
def exclude_project_participant(
        project_id: int,
        user: str = Query(..., description="Login of the user to exclude"),
        current_user = Depends(oauth2.get_current_user),
        db: Session = Depends(get_db)
):
    projects_services.delete_participant(project_id, user, current_user, db)

    return


@router.get("/{project_id}/share")
def share_project(
    request: Request,
    project_id: int,
    email: pydantic.EmailStr = Query(..., description="Email of the user to invite", alias="with"),
    current_user = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
):
    token = projects_services.share_participation(
        project_id,
        current_user,
        db
    )
    base_url = request.url_for("join_project")
    share_url = f"{base_url}?{urlencode({'token': token})}"

    return {"Emulate sending email": f"Sending access link to email: {email}",
            "Access Link attached to email": share_url}


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    background_tasks: BackgroundTasks,
    current_user=Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)):

    projects_services.delete_project(project_id, background_tasks, current_user, db)

    return

@router.post("/{project_id}/documents", status_code=status.HTTP_201_CREATED)
async def upload_project_documents(
    project_id: int,
    files: List[UploadFile] = File(...),
    current_user=Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)):

    project_docs = documents_services.upload_project_related_docs(project_id, files, current_user, db)

    return {"message": f"{len(project_docs)} doc(s) were downloaded"}

@router.get("/{project_id}/documents", response_model=list[schemas.FilesOut], status_code=status.HTTP_200_OK)
async def get_project_documents(
    project_id: int,
    current_user=Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)):

    project_docs = documents_services.get_project_related_docs(project_id, current_user, db)

    return project_docs