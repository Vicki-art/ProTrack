from fastapi import FastAPI

from app.routers import auth, projects, documents, users
from app.exceptions.exception_handlers import register_exception_handlers
from app.core.logger import setup_logger
from app.middleware.logging_middleware import logging_middleware

setup_logger()

app = FastAPI(title="Project Management App")

app.middleware("http")(logging_middleware)

register_exception_handlers(app)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(documents.router, prefix="/documents", tags=["documents"])


@app.get("/")
def root():
    return {"message": "Project Management App is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
