from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_projects():
    return {"message": "list projects"}

@router.post("/")
def create_project():
    return {"message": "create project"}