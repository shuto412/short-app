from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from typing import Optional, Dict
import logging
import os

from app.modules.scraper import Scraper
from app.modules.summarizer import ClaudeClient
from app.modules.script_generator import ScriptGenerator
from app.modules.voice_generator import VoiceGenerator
from app.modules.subtitle_generator import SubtitleGenerator
from app.modules.file_manager import FileManager
from app.api.project import projects_db, update_project_status
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/generate", tags=["generation"])

# モジュールの初期化
scraper = Scraper()
try:
    claude_client = ClaudeClient()
except ValueError as e:
    logger.warning(f"Claude client initialization failed: {e}")
    claude_client = None

script_generator = ScriptGenerator(claude_client)
voice_generator = VoiceGenerator()
subtitle_generator = SubtitleGenerator()
file_manager = FileManager()

async def process_project_task(project_id: str, url: str, scenario_type: str, voice_actor_id: str = None):
    """バックグラウンドでプロジェクト処理を実行"""
    try:
        logger.info(f"Starting project processing: {project_id}")
        
        # プロジェクトステータス更新
        update_project_status(project_id, "processing")
        
        # 1. スクレイピング
        logger.info(f"Step 1: Scraping {url}")
        scraped_content = await scraper.scrape(url)
        await file_manager.save_file(project_id, "scraped_content.txt", scraped_content)
        
        # 2. 要約生成
        logger.info("Step 2: Generating summary")
        if claude_client:
            try:
                summary = await claude_client.summarize(scraped_content)
            except Exception as e:
                logger.warning(f"Claude summarization failed: {e}, using fallback")
                summary = scraped_content[:500] + "..." if len(scraped_content) > 500 else scraped_content
        else:
            summary = scraped_content[:500] + "..." if len(scraped_content) > 500 else scraped_content
        
        await file_manager.save_file(project_id, "summary.txt", summary)
        
        # 3. 台本生成
        logger.info("Step 3: Generating script")
        script = await script_generator.generate(summary, scenario_type)
        script["metadata"]["project_id"] = project_id
        await file_manager.save_file(project_id, "script.yaml", script)
        
        # 4. ボイスアクター選択（指定がない場合はデフォルト）
        if not voice_actor_id:
            voice_actors = await voice_generator.get_voice_actors()
            if voice_actors:
                voice_actor_id = voice_actors[0]["id"]
            else:
                voice_actor_id = "mock-voice-001"
        
        # 5. 音声生成用プロンプト作成
        logger.info("Step 4: Creating voice prompt")
        voice_prompt = voice_generator.create_voice_prompt(script, voice_actor_id)
        await file_manager.save_file(project_id, "voice_prompt.yaml", voice_prompt)
        
        # 6. 音声生成
        logger.info("Step 5: Generating audio")
        audio_data = await voice_generator.generate_from_script(voice_prompt)
        await file_manager.save_file(project_id, "audio.wav", audio_data)
        
        # 7. 字幕生成
        logger.info("Step 6: Generating subtitles")
        subtitle = subtitle_generator.generate_srt(script)
        await file_manager.save_file(project_id, "subtitle.srt", subtitle)
        
        # WebVTT字幕も生成
        vtt_subtitle = subtitle_generator.generate_vtt(script)
        await file_manager.save_file(project_id, "subtitle.vtt", vtt_subtitle)
        
        # ステータス更新
        update_project_status(project_id, "completed")
        logger.info(f"Project processing completed: {project_id}")
        
    except Exception as e:
        logger.error(f"Project processing failed for {project_id}: {str(e)}")
        update_project_status(project_id, "failed")
        
        # エラー情報をファイルに保存
        error_info = {
            "error": str(e),
            "step": "processing",
            "timestamp": "2024-01-01T12:00:00"  # 実際は現在時刻
        }
        await file_manager.save_file(project_id, "error.json", error_info)

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
    background_tasks.add_task(
        process_project_task,
        project_id,
        project.url,
        project.scenario_type,
        voice_actor_id
    )
    
    return {
        "message": "Processing started",
        "project_id": project_id
    }

@router.post("/scrape")
async def scrape_url(project_id: str, url: str):
    """スクレイピング実行"""
    try:
        scraped_content = await scraper.scrape(url)
        await file_manager.save_file(project_id, "scraped_content.txt", scraped_content)
        
        return {
            "message": "Scraping completed",
            "content_length": len(scraped_content)
        }
    except Exception as e:
        logger.error(f"Scraping failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Scraping failed")

@router.post("/summary")
async def generate_summary(project_id: str):
    """要約生成"""
    try:
        # スクレイピング済みコンテンツを読み込み
        scraped_content = await file_manager.read_file(project_id, "scraped_content.txt")
        
        if claude_client:
            summary = await claude_client.summarize(scraped_content)
        else:
            # フォールバック要約
            summary = scraped_content[:500] + "..." if len(scraped_content) > 500 else scraped_content
        
        await file_manager.save_file(project_id, "summary.txt", summary)
        
        return {
            "message": "Summary generated",
            "summary_length": len(summary)
        }
    except Exception as e:
        logger.error(f"Summary generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Summary generation failed")

@router.post("/script")
async def generate_script(project_id: str, scenario_type: str):
    """台本生成"""
    try:
        # 要約を読み込み
        summary = await file_manager.read_file(project_id, "summary.txt")
        
        # 台本生成
        script = await script_generator.generate(summary, scenario_type)
        script["metadata"]["project_id"] = project_id
        
        await file_manager.save_file(project_id, "script.yaml", script)
        
        return {
            "message": "Script generated",
            "scenes_count": len(script["scenes"])
        }
    except Exception as e:
        logger.error(f"Script generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Script generation failed")

@router.post("/voice")
async def generate_voice(project_id: str, voice_actor_id: Optional[str] = None):
    """音声生成"""
    try:
        # 台本を読み込み
        script = await file_manager.read_file(project_id, "script.yaml")
        
        # デフォルトボイスアクター選択
        if not voice_actor_id:
            voice_actors = await voice_generator.get_voice_actors()
            voice_actor_id = voice_actors[0]["id"] if voice_actors else "mock-voice-001"
        
        # 音声プロンプト作成
        voice_prompt = voice_generator.create_voice_prompt(script, voice_actor_id)
        await file_manager.save_file(project_id, "voice_prompt.yaml", voice_prompt)
        
        # 音声生成
        audio_data = await voice_generator.generate_from_script(voice_prompt)
        await file_manager.save_file(project_id, "audio.wav", audio_data)
        
        return {
            "message": "Voice generated",
            "audio_size": len(audio_data)
        }
    except Exception as e:
        logger.error(f"Voice generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Voice generation failed")

@router.post("/subtitle")
async def generate_subtitle(project_id: str):
    """字幕生成"""
    try:
        # 台本を読み込み
        script = await file_manager.read_file(project_id, "script.yaml")
        
        # SRT字幕生成
        srt_subtitle = subtitle_generator.generate_srt(script)
        await file_manager.save_file(project_id, "subtitle.srt", srt_subtitle)
        
        # WebVTT字幕生成
        vtt_subtitle = subtitle_generator.generate_vtt(script)
        await file_manager.save_file(project_id, "subtitle.vtt", vtt_subtitle)
        
        return {
            "message": "Subtitles generated",
            "formats": ["srt", "vtt"]
        }
    except Exception as e:
        logger.error(f"Subtitle generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Subtitle generation failed")

@router.get("/voice-actors")
async def get_voice_actors():
    """利用可能なボイスアクター一覧を取得"""
    try:
        voice_actors = await voice_generator.get_voice_actors()
        return {"voice_actors": voice_actors}
    except Exception as e:
        logger.error(f"Voice actors retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get voice actors")

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