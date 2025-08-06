"""
改善版: 段階的処理専用APIエンドポイント
すべての処理を段階的に実行し、ユーザーの明示的な指示でのみ進行する
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from typing import Optional, Dict, List
import logging
import os
from pydantic import BaseModel

from app.modules.stage_processor import StageProcessor
from app.modules.file_manager import FileManager
from app.modules.script_editor import ScriptEditor
from app.modules.voice_prompt_editor import VoicePromptEditor
from app.modules.voice_generator import VoiceGenerator
from app.api.project import projects_db, update_project_status
from app.models.project import ProjectStage
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/stages", tags=["stages"])

# モジュールの初期化
stage_processor = StageProcessor()
file_manager = FileManager()
script_editor = ScriptEditor()
voice_prompt_editor = VoicePromptEditor()
voice_generator = VoiceGenerator()

# リクエストモデル
class ScriptGenerationRequest(BaseModel):
    project_id: str
    scenario_type: str

# =============================================================================
# 段階実行エンドポイント（改善版）
# =============================================================================

@router.post("/scraping")
async def execute_scraping(
    project_id: str,
    background_tasks: BackgroundTasks
):
    """段階1: スクレイピング実行"""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = projects_db[project_id]
    
    # 現在の段階が適切かチェック
    if project.current_stage != ProjectStage.URL_INPUT:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid stage. Current: {project.current_stage}, Expected: {ProjectStage.URL_INPUT}"
        )
    
    try:
        logger.info(f"🌐 Starting scraping stage for project {project_id}")
        
        # バックグラウンドでスクレイピング実行
        async def scraping_task():
            try:
                update_project_status(project_id, "processing")
                projects_db[project_id].current_stage = ProjectStage.SCRAPING
                
                result = await stage_processor.process_stage_scraping(project_id, project.url)
                
                if result["success"]:
                    update_project_status(project_id, "ready")
                    projects_db[project_id].current_stage = ProjectStage.SUMMARIZING
                    logger.info(f"✅ Scraping completed for {project_id}")
                else:
                    update_project_status(project_id, "failed")
                    logger.error(f"❌ Scraping failed for {project_id}")
                    
            except Exception as e:
                logger.error(f"❌ Scraping task failed for {project_id}: {str(e)}")
                update_project_status(project_id, "failed")
        
        background_tasks.add_task(scraping_task)
        
        return {
            "message": "スクレイピングを開始しました",
            "project_id": project_id,
            "current_stage": ProjectStage.SCRAPING,
            "next_stage": ProjectStage.SUMMARIZING
        }
        
    except Exception as e:
        logger.error(f"❌ Scraping execution failed for {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="スクレイピングの実行に失敗しました")

@router.post("/summary")
async def execute_summary(
    project_id: str,
    background_tasks: BackgroundTasks
):
    """段階2: 要約生成実行"""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = projects_db[project_id]
    
    # 前段階の完了をチェック
    if not file_manager.file_exists(project_id, "scraped_content.txt"):
        raise HTTPException(status_code=400, detail="スクレイピングが完了していません")
    
    try:
        logger.info(f"📝 Starting summary generation stage for project {project_id}")
        
        # バックグラウンドで要約生成実行
        async def summary_task():
            try:
                update_project_status(project_id, "processing")
                projects_db[project_id].current_stage = ProjectStage.SUMMARIZING
                
                result = await stage_processor.process_stage_summary(project_id)
                
                if result["success"]:
                    update_project_status(project_id, "ready")
                    projects_db[project_id].current_stage = ProjectStage.SCRIPT_GENERATING
                    logger.info(f"✅ Summary generation completed for {project_id}")
                else:
                    update_project_status(project_id, "failed")
                    logger.error(f"❌ Summary generation failed for {project_id}")
                    
            except Exception as e:
                logger.error(f"❌ Summary generation task failed for {project_id}: {str(e)}")
                update_project_status(project_id, "failed")
        
        background_tasks.add_task(summary_task)
        
        return {
            "message": "要約生成を開始しました",
            "project_id": project_id,
            "current_stage": ProjectStage.SUMMARIZING,
            "next_stage": ProjectStage.SCRIPT_GENERATING
        }
        
    except Exception as e:
        logger.error(f"❌ Summary generation execution failed for {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="要約生成の実行に失敗しました")

@router.post("/script")
async def execute_script_generation(
    request: ScriptGenerationRequest,
    background_tasks: BackgroundTasks
):
    """段階3: 台本生成実行"""
    project_id = request.project_id
    scenario_type = request.scenario_type
    
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # 前段階の完了をチェック
    if not file_manager.file_exists(project_id, "summary.txt"):
        raise HTTPException(status_code=400, detail="要約生成が完了していません")
    
    try:
        logger.info(f"🎬 Starting script generation stage for project {project_id}")
        
        # バックグラウンドで台本生成実行
        async def script_task():
            try:
                update_project_status(project_id, "processing")
                projects_db[project_id].current_stage = ProjectStage.SCRIPT_GENERATING
                
                result = await stage_processor.process_stage_script_generation(project_id, scenario_type)
                
                if result["success"]:
                    update_project_status(project_id, "ready")
                    projects_db[project_id].current_stage = ProjectStage.SCRIPT_EDITING
                    projects_db[project_id].can_edit_script = True
                    logger.info(f"✅ Script generation completed for {project_id}")
                else:
                    update_project_status(project_id, "failed")
                    logger.error(f"❌ Script generation failed for {project_id}")
                    
            except Exception as e:
                logger.error(f"❌ Script generation task failed for {project_id}: {str(e)}")
                update_project_status(project_id, "failed")
        
        background_tasks.add_task(script_task)
        
        return {
            "message": "台本生成を開始しました",
            "project_id": project_id,
            "current_stage": ProjectStage.SCRIPT_GENERATING,
            "next_stage": ProjectStage.SCRIPT_EDITING
        }
        
    except Exception as e:
        logger.error(f"❌ Script generation execution failed for {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="台本生成の実行に失敗しました")

# =============================================================================
# 台本編集エンドポイント
# =============================================================================

@router.get("/script/{project_id}")
async def get_script(project_id: str):
    """台本取得"""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not file_manager.file_exists(project_id, "script.yaml"):
        raise HTTPException(status_code=404, detail="台本が見つかりません。まず台本を生成してください")
    
    try:
        result = await script_editor.get_script(project_id)
        if result["success"]:
            return result["script"]
        else:
            raise HTTPException(status_code=500, detail=result.get("message", "台本の取得に失敗しました"))
    except Exception as e:
        logger.error(f"❌ Failed to get script for {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"台本の取得に失敗しました: {str(e)}")

@router.put("/script/{project_id}")
async def update_script(project_id: str, script_update: Dict):
    """台本編集"""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = projects_db[project_id]
    if not project.can_edit_script:
        raise HTTPException(status_code=400, detail="台本編集が許可されていません")
    
    try:
        result = await script_editor.update_script(project_id, script_update)
        if result["success"]:
            return {
                "message": result["message"],
                "warnings": result.get("warnings", []),
                "script": result["script"]
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("message", "台本の更新に失敗しました"))
    except Exception as e:
        logger.error(f"❌ Failed to update script for {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"台本の更新に失敗しました: {str(e)}")

# =============================================================================
# 音声設定作成・編集エンドポイント
# =============================================================================

@router.post("/voice-settings")
async def execute_voice_settings_creation(
    project_id: str,
    voice_actor_id: str,
    background_tasks: BackgroundTasks,
    voice_speed: float = 1.0
):
    """段階4: 音声設定作成実行"""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = projects_db[project_id]
    
    # 前段階の完了をチェック
    if not file_manager.file_exists(project_id, "script.yaml"):
        raise HTTPException(status_code=400, detail="台本生成が完了していません")
    
    try:
        logger.info(f"🎙️ Starting voice settings creation for project {project_id}")
        
        # バックグラウンドで音声設定作成実行
        async def voice_settings_task():
            try:
                update_project_status(project_id, "processing")
                projects_db[project_id].current_stage = ProjectStage.VOICE_SETTINGS_EDITING
                
                result = await stage_processor.process_stage_voice_prompt_creation(
                    project_id, voice_actor_id, voice_speed
                )
                
                if result["success"]:
                    update_project_status(project_id, "ready")
                    projects_db[project_id].current_stage = ProjectStage.VOICE_GENERATING
                    projects_db[project_id].can_edit_voice = True
                    logger.info(f"✅ Voice settings creation completed for {project_id}")
                else:
                    update_project_status(project_id, "failed")
                    logger.error(f"❌ Voice settings creation failed for {project_id}")
                    
            except Exception as e:
                logger.error(f"❌ Voice settings creation task failed for {project_id}: {str(e)}")
                update_project_status(project_id, "failed")
        
        background_tasks.add_task(voice_settings_task)
        
        return {
            "message": "音声設定作成を開始しました",
            "project_id": project_id,
            "current_stage": ProjectStage.VOICE_SETTINGS_EDITING,
            "next_stage": ProjectStage.VOICE_GENERATING
        }
        
    except Exception as e:
        logger.error(f"❌ Voice settings creation execution failed for {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="音声設定作成の実行に失敗しました")

@router.get("/voice-settings/{project_id}")
async def get_voice_settings(project_id: str):
    """音声設定取得"""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not file_manager.file_exists(project_id, "voice_prompt.yaml"):
        raise HTTPException(status_code=404, detail="音声設定が見つかりません。まず音声設定を作成してください")
    
    try:
        result = await voice_prompt_editor.get_voice_prompt(project_id)
        if result["success"]:
            return result["voice_prompt"]
        else:
            raise HTTPException(status_code=500, detail=result.get("message", "音声設定の取得に失敗しました"))
    except Exception as e:
        logger.error(f"❌ Failed to get voice settings for {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"音声設定の取得に失敗しました: {str(e)}")

@router.put("/voice-settings/{project_id}")
async def update_voice_settings(project_id: str, settings_update: Dict):
    """音声設定編集"""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = projects_db[project_id]
    if not project.can_edit_voice:
        raise HTTPException(status_code=400, detail="音声設定編集が許可されていません")
    
    try:
        result = await voice_prompt_editor.update_voice_prompt(project_id, settings_update)
        if result["success"]:
            return {
                "message": result["message"],
                "warnings": result.get("warnings", []),
                "voice_prompt": result["voice_prompt"]
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("message", "音声設定の更新に失敗しました"))
    except Exception as e:
        logger.error(f"❌ Failed to update voice settings for {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"音声設定の更新に失敗しました: {str(e)}")

# =============================================================================
# 音声生成エンドポイント
# =============================================================================

@router.post("/voice-generation")
async def execute_voice_generation(
    project_id: str,
    background_tasks: BackgroundTasks
):
    """段階5: 音声・字幕生成実行"""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = projects_db[project_id]
    
    # 前段階の完了をチェック
    if not file_manager.file_exists(project_id, "voice_prompt.yaml"):
        raise HTTPException(status_code=400, detail="音声設定作成が完了していません")
    
    try:
        logger.info(f"🎵 Starting voice generation for project {project_id}")
        
        # バックグラウンドで音声生成実行
        async def voice_generation_task():
            try:
                update_project_status(project_id, "processing")
                projects_db[project_id].current_stage = ProjectStage.VOICE_GENERATING
                
                result = await stage_processor.process_stage_voice_generation(project_id)
                
                if result["success"]:
                    update_project_status(project_id, "ready")
                    projects_db[project_id].current_stage = ProjectStage.COMPLETED
                    logger.info(f"✅ Voice generation completed for {project_id}")
                else:
                    update_project_status(project_id, "failed")
                    logger.error(f"❌ Voice generation failed for {project_id}")
                    
            except Exception as e:
                logger.error(f"❌ Voice generation task failed for {project_id}: {str(e)}")
                update_project_status(project_id, "failed")
        
        background_tasks.add_task(voice_generation_task)
        
        return {
            "message": "音声・字幕生成を開始しました",
            "project_id": project_id,
            "current_stage": ProjectStage.VOICE_GENERATING,
            "next_stage": ProjectStage.COMPLETED
        }
        
    except Exception as e:
        logger.error(f"❌ Voice generation execution failed for {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="音声生成の実行に失敗しました")

# =============================================================================
# 参照データエンドポイント
# =============================================================================

@router.get("/voice-actors")
async def get_voice_actors():
    """利用可能なボイスアクター一覧を取得"""
    try:
        voice_actors = await voice_generator.get_voice_actors()
        return {"voice_actors": voice_actors}
    except Exception as e:
        logger.error(f"Voice actors retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail="ボイスアクター一覧の取得に失敗しました")

@router.get("/scenarios")
async def get_scenarios():
    """シナリオテンプレート一覧"""
    return {
        "scenarios": [
            {
                "id": "product_introduction",
                "name": "製品紹介",
                "description": "製品の特徴や利点を紹介",
                "category": "ビジネス"
            },
            {
                "id": "tutorial",
                "name": "チュートリアル",
                "description": "ステップバイステップの説明",
                "category": "教育"
            },
            {
                "id": "feature_explanation",
                "name": "機能説明",
                "description": "特定機能の詳細説明",
                "category": "解説"
            },
            {
                "id": "news_report",
                "name": "ニュース報道",
                "description": "ニュースや情報の報告",
                "category": "報道"
            },
            {
                "id": "review",
                "name": "レビュー",
                "description": "製品やサービスの評価",
                "category": "評価"
            },
            {
                "id": "comparison",
                "name": "比較検討",
                "description": "複数の選択肢の比較",
                "category": "比較"
            },
            {
                "id": "interview",
                "name": "インタビュー",
                "description": "専門家との対談形式",
                "category": "対話"
            },
            {
                "id": "event_coverage",
                "name": "イベント取材",
                "description": "イベントやセミナーの案内",
                "category": "イベント"
            },
            {
                "id": "storytelling",
                "name": "ストーリーテリング",
                "description": "感情的な体験の物語",
                "category": "物語"
            }
        ]
    }

# =============================================================================
# ファイルダウンロードエンドポイント
# =============================================================================

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
        "voice-settings": "voice_prompt.yaml"
    }
    
    if file_type not in file_mapping:
        raise HTTPException(status_code=400, detail="無効なファイルタイプです")
    
    filename = file_mapping[file_type]
    file_path = file_manager.get_file_path(project_id, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="ファイルが見つかりません")
    
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