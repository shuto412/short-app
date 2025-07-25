from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api import project, generation
from app.config import settings
import logging

# ロガー設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="URL Video Script Generator", version="1.0.0")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React開発サーバー
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ヘルスチェックエンドポイント追加
@app.get("/health")
async def health_check():
    """API サーバーのヘルスチェック"""
    return {"status": "healthy", "message": "URL Video Script Generator API is running"}

# ルーター登録
app.include_router(project.router, prefix="/api/project", tags=["project"])
app.include_router(project.router, prefix="/api/projects", tags=["project"])  # フロントエンド互換性
app.include_router(generation.router, prefix="/api/generate", tags=["generation"])

# 静的ファイル配信 (テンプレートディレクトリが存在する場合のみ)
import os
if os.path.exists("templates"):
    app.mount("/", StaticFiles(directory="templates", html=True), name="static")

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 URL Video Script Generator API started")

@app.on_event("shutdown") 
async def shutdown_event():
    logger.info("🛑 URL Video Script Generator API stopped")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
