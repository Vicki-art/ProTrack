from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_documents():
    return {"message": "list documents"}