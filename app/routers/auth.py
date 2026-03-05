from fastapi import APIRouter

router = APIRouter()

@router.post("/auth")
def register():
    return {"message": "register endpoint"}

@router.post("/login")
def login():
    return {"message": "login endpoint"}