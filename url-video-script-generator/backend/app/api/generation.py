from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from typing import Optional, Dict
import logging
import os

from app.modules.scraper import Scraper
from app.modules.script_generator import ScriptGenerator
from app.modules.voice_generator import VoiceGenerator
from app.modules.subtitle_generator import SubtitleGenerator
from app.modules.file_manager import FileManager
from app.api.project import projects_db, update_project_status

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/generate", tags=["generation"])

# モジュールの初期化
scraper = Scraper()
try:
    from app.modules.summarizer import ClaudeClient
    claude_client = ClaudeClient()
except Exception as e:
    logger.warning(f"Claude client initialization failed: {e}")
    claude_client = None

script_generator = ScriptGenerator(claude_client)
voice_generator = VoiceGenerator()
subtitle_generator = SubtitleGenerator()
file_manager = FileManager()

@router.get("/scenarios")
async def get_scenarios():
    """シナリオテンプレート一覧"""
    return {
        "scenarios": [
            {
                "id": "product_introduction",
                "name": "製品紹介",
                "description": "製品の特徴や利点を紹介"
            },
            {
                "id": "tutorial", 
                "name": "使い方説明",
                "description": "ステップバイステップの説明"
            },
            {
                "id": "feature_explanation",
                "name": "機能説明",
                "description": "特定機能の詳細説明"
            }
        ]
    }

@router.get("/voice-actors")
async def get_voice_actors():
    """利用可能なボイスアクター一覧を取得"""
    try:
        voice_actors = await voice_generator.get_voice_actors()
        return {"voice_actors": voice_actors}
    except Exception as e:
        logger.error(f"Voice actors retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get voice actors")

@router.post("/process")
async def process_full(
    project_id: str,
    background_tasks: BackgroundTasks,
    voice_actor_id: Optional[str] = None
):
    """フル処理実行"""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = projects_db[project_id]
    
    # バックグラウンドタスクとして実行
    async def process_task():
        try:
            logger.info(f"Starting project processing: {project_id}")
            update_project_status(project_id, "processing")
            
            # 1. スクレイピング
            scraped_content = await scraper.scrape(project.url)
            await file_manager.save_file(project_id, "scraped_content.txt", scraped_content)
            
            # 2. 要約生成
            if claude_client:
                try:
                    summary = await claude_client.summarize(scraped_content)
                except Exception:
                    summary = scraped_content[:500] + "..." if len(scraped_content) > 500 else scraped_content
            else:
                summary = scraped_content[:500] + "..." if len(scraped_content) > 500 else scraped_content
            
            await file_manager.save_file(project_id, "summary.txt", summary)
            
            # 3. 台本生成
            script = await script_generator.generate(summary, project.scenario_type)
            script["metadata"]["project_id"] = project_id
            await file_manager.save_file(project_id, "script.yaml", script)
            
            # 4. 音声生成
            if not voice_actor_id:
                voice_actors = await voice_generator.get_voice_actors()
                voice_actor_id = voice_actors[0]["id"] if voice_actors else "mock-voice-001"
            
            voice_prompt = voice_generator.create_voice_prompt(script, voice_actor_id)
            await file_manager.save_file(project_id, "voice_prompt.yaml", voice_prompt)
            
            audio_data = await voice_generator.generate_from_script(voice_prompt)
            await file_manager.save_file(project_id, "audio.wav", audio_data)
            
            # 5. 字幕生成
            subtitle = subtitle_generator.generate_srt(script)
            await file_manager.save_file(project_id, "subtitle.srt", subtitle)
            
            vtt_subtitle = subtitle_generator.generate_vtt(script)
            await file_manager.save_file(project_id, "subtitle.vtt", vtt_subtitle)
            
            update_project_status(project_id, "completed")
            logger.info(f"Project processing completed: {project_id}")
            
        except Exception as e:
            logger.error(f"Project processing failed for {project_id}: {str(e)}")
            update_project_status(project_id, "failed")
    
    background_tasks.add_task(process_task)
    
    return {
        "message": "Processing started",
        "project_id": project_id
    }

@router.get("/download/{project_id}/{file_type}")
async def download_file(project_id: str, file_type: str):
    """ファイルダウンロード"""
    file_mapping = {
        "script": "script.yaml",
        "audio": "audio.wav",
        "subtitle": "subtitle.srt",
        "subtitle-vtt": "subtitle.vtt",
        "summary": "summary.txt",
        "content": "scraped_content.txt",
        "voice-prompt": "voice_prompt.yaml"
    }
    
    if file_type not in file_mapping:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    filename = file_mapping[file_type]
    file_path = file_manager.get_file_path(project_id, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # MIMEタイプの設定
    media_type = "application/octet-stream"
    if filename.endswith('.txt'):
        media_type = "text/plain"
    elif filename.endswith('.yaml'):
        media_type = "application/x-yaml"
    elif filename.endswith('.wav'):
        media_type = "audio/wav"
    elif filename.endswith('.srt'):
        media_type = "application/x-subrip"
    elif filename.endswith('.vtt'):
        media_type = "text/vtt"
    
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename
    )
