from fastapi import FastAPI
from app.routers import auth, projects, documents

app = FastAPI(title="Project Management Service")

app.include_router(auth.router, prefix="", tags=["auth"])
app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(documents.router, prefix="/documents", tags=["documents"])

@app.get("/")
def root():
    return {"message": "Project Management Service is running"}

def register():
    return {"message": "Project Management Service is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
