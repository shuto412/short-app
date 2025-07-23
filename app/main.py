from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.project import router as project_router
from app.api.generation import router as generation_router

app = FastAPI(title="URL Video Script Generator")

# CORS設定を強化
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ルーターを追加
app.include_router(project_router)
app.include_router(generation_router)

@app.get("/")
def read_root():
    return {"message": "URL Video Script Generator API"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "URL Video Script Generator"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.BACKEND_PORT) 