from fastapi import APIRouter, Depends
from app import oauth2, schemas

router = APIRouter()

#Trying route for only authenticated user
@router.get("/")
def get_projects(current_user = Depends(oauth2.get_current_user)):
    return {"message": "Success"}


