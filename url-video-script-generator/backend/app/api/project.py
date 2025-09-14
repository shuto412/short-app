from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Optional
import uuid
from datetime import datetime
import logging

from app.models.project import Project, ProjectCreate
from app.modules.file_manager import FileManager
from app.modules.markdown_processor import MarkdownProcessor

logger = logging.getLogger(__name__)

router = APIRouter(tags=["projects"])
file_manager = FileManager()
markdown_processor = MarkdownProcessor()

# 一時的なメモリストレージ（実際はDBを使用）
projects_db: Dict[str, Project] = {}

@router.post("/")
@router.post("")  # フロントエンドとの互換性のため両方対応
async def create_project(project: ProjectCreate):
    """新規プロジェクト作成（URL/Markdown対応）"""
    try:
        project_id = str(uuid.uuid4())
        await file_manager.create_project_dir(project_id)

        input_source = project.input_source or "url"
        url: Optional[str] = None
        markdown_filename: Optional[str] = None
        title: Optional[str] = None

        if input_source == "markdown":
            if not project.markdown_content:
                raise HTTPException(status_code=400, detail="markdown_content is required")
            markdown_filename = project.markdown_filename or "markdown.md"
            await file_manager.save_file(project_id, "markdown.md", project.markdown_content)
            meta = await markdown_processor.extract_metadata(project.markdown_content)
            title = (meta.get("title") or "Markdown - 動画制作プロジェクト")
        else:
            if not project.url:
                raise HTTPException(status_code=400, detail="url is required")
            url = project.url
            title = _generate_title_from_url(url)

        new_project = Project(
            id=project_id,
            url=url,
            title=title,
            input_source=input_source,
            markdown_filename=markdown_filename,
            scenario_type=project.scenario_type,
            status="created",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        projects_db[project_id] = new_project
        logger.info(f"Created project {project_id} (source={input_source})")

        return {
            "project_id": project_id,
            "status": "created",
            "message": "Project created successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Project creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create project")

@router.get("/{project_id}")
async def get_project(project_id: str):
    """プロジェクト情報取得"""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = projects_db[project_id]
    
    # プロジェクトファイル一覧も含める
    files = file_manager.list_project_files(project_id)
    
    return {
        "project": {
            "id": project.id,
            "url": project.url,
            "title": project.title,
            "input_source": project.input_source,
            "markdown_filename": project.markdown_filename,
            "scenario_type": project.scenario_type,
            "status": project.status,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat()
        },
        "files": files
    }

@router.get("/{project_id}/status")
async def get_project_status(project_id: str):
    """処理状況取得"""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = projects_db[project_id]
    files = file_manager.list_project_files(project_id)
    
    # ファイルの存在確認で進捗を判定
    progress = _calculate_progress(project_id, files)
    
    return {
        "project_id": project_id,
        "status": project.status,
        "progress": progress,
        "files": files,
        "last_updated": project.updated_at.isoformat()
    }

@router.get("/")
async def list_projects():
    """プロジェクト一覧取得"""
    projects_list = []
    
    for project in projects_db.values():
        files = file_manager.list_project_files(project.id)
        progress = _calculate_progress(project.id, files)
        
        projects_list.append({
            "id": project.id,
            "title": project.title,
            "url": project.url,
            "input_source": project.input_source,
            "markdown_filename": project.markdown_filename,
            "scenario_type": project.scenario_type,
            "status": project.status,
            "progress": progress,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat()
        })
    
    return {
        "projects": projects_list,
        "total": len(projects_list)
    }

def update_project_status(project_id: str, status: str):
    """プロジェクトステータス更新（内部関数）"""
    if project_id in projects_db:
        projects_db[project_id].status = status
        projects_db[project_id].updated_at = datetime.now()
        logger.info(f"Updated project {project_id} status to {status}")

def _generate_title_from_url(url: str) -> str:
    """URLからプロジェクトタイトルを生成"""
    from urllib.parse import urlparse
    
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        
        # ドメイン名からタイトルを生成
        if domain:
            return f"{domain} - 動画制作プロジェクト"
        else:
            return "動画制作プロジェクト"
    except:
        return "動画制作プロジェクト"

def _calculate_progress(project_id: str, files: List[str]) -> Dict:
    """ファイル存在確認で進捗を計算"""
    required_files = [
        "scraped_content.txt",
        "summary.txt",
        "summary.yaml",
        "script.yaml",
        "voice_prompt.yaml",
        "audio.wav",
        "subtitle.srt"
    ]
    
    completed_steps = []
    total_steps = len(required_files)
    
    step_names = [
        "スクレイピング",
        "要約生成（テキスト）",
        "要約生成（構造化）",
        "台本生成", 
        "音声プロンプト作成",
        "音声生成",
        "字幕生成"
    ]
    
    for i, file_name in enumerate(required_files):
        completed = False
        reported_file = file_name
        if i == 0:
            if file_name in files:
                completed = True
            elif "markdown.md" in files:
                completed = True
                reported_file = "markdown.md"
        else:
            completed = file_name in files

        completed_steps.append({
            "step": step_names[i],
            "completed": completed,
            "file": reported_file
        })
    
    completed_count = sum(1 for step in completed_steps if step["completed"])
    progress_percentage = (completed_count / total_steps) * 100
    
    return {
        "percentage": round(progress_percentage, 1),
        "completed_steps": completed_count,
        "total_steps": total_steps,
        "steps": completed_steps
    }
