from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from typing import Optional, Dict
import logging
import os
from datetime import datetime

from app.modules.scraper import Scraper
from app.modules.script_generator import ScriptGenerator
from app.modules.voice_generator import VoiceGenerator
from app.modules.subtitle_generator import SubtitleGenerator
from app.modules.file_manager import FileManager
from app.api.project import projects_db, update_project_status

logger = logging.getLogger(__name__)

router = APIRouter(tags=["generation"])

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
    """シナリオテンプレート一覧（簡略版）"""
    try:
        templates_data = script_generator.get_available_templates()
        templates = templates_data.get("templates", {})
        
        scenarios = []
        for template_id, template_info in templates.items():
            # テンプレートファイルから名前と説明を読み込み
            try:
                template = script_generator._load_template(template_id)
                scenarios.append({
                    "id": template_id,
                    "name": template.get("name", template_id),
                    "description": template.get("description", "シナリオテンプレート"),
                    "category": template_info.get("category", "その他")
                })
            except Exception as e:
                logger.warning(f"Failed to load template {template_id}: {str(e)}")
                continue
        
        return {"scenarios": scenarios}
        
    except Exception as e:
        logger.error(f"Failed to get scenarios: {str(e)}")
        # フォールバック（最低限のテンプレート）
        return {
            "scenarios": [
                {
                    "id": "product_introduction",
                    "name": "製品紹介",
                    "description": "製品の特徴や利点を紹介",
                    "category": "ビジネス"
                }
            ]
        }

@router.get("/templates")
async def get_templates():
    """テンプレート詳細情報一覧"""
    try:
        templates_data = script_generator.get_available_templates()
        templates = templates_data.get("templates", {})
        
        detailed_templates = {}
        for template_id, template_info in templates.items():
            try:
                template = script_generator._load_template(template_id)
                detailed_templates[template_id] = {
                    "name": template.get("name", template_id),
                    "description": template.get("description", "シナリオテンプレート"),
                    "category": template_info.get("category", "その他"),
                    "tags": template_info.get("tags", []),
                    "structure": template.get("structure", []),
                    "voice_settings": template.get("voice_settings", {}),
                    "file": template_info.get("file")
                }
            except Exception as e:
                logger.warning(f"Failed to load template {template_id}: {str(e)}")
                continue
        
        return {
            "templates": detailed_templates,
            "total_count": len(detailed_templates)
        }
        
    except Exception as e:
        logger.error(f"Failed to get templates: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to load templates")

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
            logger.info(f"Background task started for project: {project_id}")
            logger.info(f"Starting project processing: {project_id}")
            update_project_status(project_id, "processing")
            
            # voice_actor_idをローカル変数として初期化（外側の関数パラメータから値をコピー）
            selected_voice_actor_id = voice_actor_id
            
            # 1. スクレイピング
            scraped_content = await scraper.scrape(project.url)
            await file_manager.save_file(project_id, "scraped_content.txt", scraped_content)
            
            # 2. 要約生成
            logger.info(f"Starting summary generation for project: {project_id}")
            
            # まずテキスト要約を生成・保存
            if claude_client:
                try:
                    text_summary = await claude_client.summarize(scraped_content)
                    await file_manager.save_file(project_id, "summary.txt", text_summary)
                    logger.info(f"Text summary saved for project: {project_id}")
                except Exception as e:
                    logger.warning(f"Text summary generation failed: {str(e)}")
                    summary = scraped_content[:500] + "..." if len(scraped_content) > 500 else scraped_content
                    await file_manager.save_file(project_id, "summary.txt", summary)
            else:
                summary = scraped_content[:500] + "..." if len(scraped_content) > 500 else scraped_content
                await file_manager.save_file(project_id, "summary.txt", summary)
            
            # 構造化要約の生成（常に試行、失敗時はフォールバック）
            summary_yaml_created = False
            
            if claude_client:
                try:
                    logger.info(f"Starting structured summary generation for project: {project_id}")
                    structured_summary = await claude_client.create_structured_summary(scraped_content)
                    
                    # メタデータを追加
                    summary_data = {
                        "metadata": {
                            "project_id": project_id,
                            "url": project.url,
                            "generated_at": datetime.now().isoformat(),
                            "content_length": len(scraped_content)
                        },
                        "product_info": structured_summary
                    }
                    
                    # YAMLファイルとして保存
                    await file_manager.save_file(project_id, "summary.yaml", summary_data)
                    logger.info(f"Structured summary YAML saved successfully for project: {project_id}")
                    summary_yaml_created = True
                    
                except Exception as e:
                    logger.error(f"Structured summary generation failed: {str(e)}")
                    # 構造化要約失敗時の処理は下で実行
            
            # 構造化要約が作成されていない場合は、必ずフォールバック版を作成
            if not summary_yaml_created:
                logger.info(f"Creating fallback structured summary for project: {project_id}")
                fallback_summary_data = {
                    "metadata": {
                        "project_id": project_id,
                        "url": project.url,
                        "generated_at": datetime.now().isoformat(),
                        "content_length": len(scraped_content),
                        "error": "構造化要約生成失敗またはClaude client未初期化",
                        "fallback": True
                    },
                    "product_info": {
                        "product_name": "製品名取得失敗",
                        "price": "価格情報取得失敗",
                        "specifications": {
                            "size": "サイズ情報なし",
                            "weight": "重量情報なし",
                            "dimensions": {},
                            "materials": "素材情報なし",
                            "other": "その他仕様なし"
                        },
                        "description": scraped_content[:200] + "..." if len(scraped_content) > 200 else scraped_content
                    }
                }
                
                await file_manager.save_file(project_id, "summary.yaml", fallback_summary_data)
                logger.info(f"Fallback summary YAML saved for project: {project_id}")
            
            # 3. 台本生成
            # summary変数が定義されていない場合は、テキスト要約を読み込む
            try:
                summary_text = await file_manager.read_file(project_id, "summary.txt")
            except Exception as e:
                logger.warning(f"Failed to read summary.txt: {str(e)}")
                summary_text = scraped_content[:500] + "..." if len(scraped_content) > 500 else scraped_content
            
            script = await script_generator.generate(summary_text, project.scenario_type)
            script["metadata"]["project_id"] = project_id
            await file_manager.save_file(project_id, "script.yaml", script)
            
            # 4. 音声生成
            if not selected_voice_actor_id:
                voice_actors = await voice_generator.get_voice_actors()
                logger.info(f"📊 取得したボイスアクターの構造: {voice_actors[0] if voice_actors else 'リストが空'}")
                
                # デフォルトIDを優先的に使用（花村 穂ノ香）
                default_voice_actor_id = "231e0170-0ece-4155-be44-231423062f41"
                
                # デフォルトIDが利用可能かチェック
                if voice_actors:
                    available_ids = []
                    for actor in voice_actors:
                        if isinstance(actor, dict) and "id" in actor:
                            available_ids.append(actor["id"])
                    
                    if default_voice_actor_id in available_ids:
                        selected_voice_actor_id = default_voice_actor_id
                        logger.info(f"🎯 デフォルトボイスアクターを使用: {selected_voice_actor_id}")
                    else:
                        # デフォルトが利用できない場合は最初のものを使用
                        first_actor = voice_actors[0]
                        selected_voice_actor_id = first_actor.get("id", "mock-voice-001")
                        logger.info(f"🎯 デフォルトが利用不可、代替を使用: {selected_voice_actor_id}")
                        logger.info(f"📋 利用可能ID: {available_ids[:3]}...")  # 最初の3つを表示
                else:
                    selected_voice_actor_id = default_voice_actor_id  # モックデータでもデフォルトIDを使用
                    
                logger.info(f"🎯 最終選択されたID: {selected_voice_actor_id} (取得数: {len(voice_actors)})")
            
            voice_prompt = voice_generator.create_voice_prompt(script, selected_voice_actor_id)
            await file_manager.save_file(project_id, "voice_prompt.yaml", voice_prompt)
            
            # 個別音声ファイル生成
            audio_files = await voice_generator.generate_individual_files_from_script(voice_prompt)
            
            # 各セグメントを個別ファイルとして保存
            for file_info in audio_files:
                await file_manager.save_file(project_id, file_info["filename"], file_info["audio_data"])
                logger.info(f"📁 保存完了: {file_info['filename']} ({file_info['size_bytes']} bytes)")
            
            # 従来の統合ファイルも生成（互換性のため）
            if audio_files:
                combined_audio = voice_generator._combine_audio_segments([f["audio_data"] for f in audio_files])
                await file_manager.save_file(project_id, "audio_combined.wav", combined_audio)
                logger.info(f"📁 統合ファイル保存完了: audio_combined.wav ({len(combined_audio)} bytes)")
            
            # 音声ファイル情報を保存
            audio_files_info = [
                {
                    "segment_id": f["segment_id"],
                    "filename": f["filename"],
                    "text": f["text"],
                    "duration": f["duration"],
                    "size_bytes": f["size_bytes"],
                    "error": f.get("error")
                }
                for f in audio_files
            ]
            await file_manager.save_file(project_id, "audio_files_info.yaml", audio_files_info)
            
            # 5. 字幕生成
            subtitle = subtitle_generator.generate_srt(script)
            await file_manager.save_file(project_id, "subtitle.srt", subtitle)
            
            vtt_subtitle = subtitle_generator.generate_vtt(script)
            await file_manager.save_file(project_id, "subtitle.vtt", vtt_subtitle)
            
            update_project_status(project_id, "completed")
            logger.info(f"Project processing completed: {project_id}")
            
        except Exception as e:
            logger.error(f"Project processing failed for {project_id}: {str(e)}")
            import traceback
            logger.error(f"Full processing error traceback: {traceback.format_exc()}")
            update_project_status(project_id, "failed")
    
    background_tasks.add_task(process_task)
    
    return {
        "message": "Processing started",
        "project_id": project_id
    }

@router.get("/download/{project_id}/segments/{segment_filename}")
async def download_audio_segment(project_id: str, segment_filename: str):
    """個別音声セグメントダウンロード"""
    logger.info(f"🎵 Individual audio download request: project={project_id}, file={segment_filename}")
    
    # セキュリティ: ファイル名検証
    if not segment_filename.startswith("audio_segment_") or not segment_filename.endswith(".wav"):
        logger.error(f"❌ Invalid filename: {segment_filename}")
        raise HTTPException(status_code=400, detail="Invalid audio segment filename")
    
    # ファイルパス取得
    file_path = file_manager.get_file_path(project_id, segment_filename)
    logger.info(f"📁 File path: {file_path}")
    logger.info(f"📂 File exists: {os.path.exists(file_path)}")
    
    if not os.path.exists(file_path):
        logger.error(f"❌ File not found: {file_path}")
        raise HTTPException(status_code=404, detail="Audio segment not found")
    
    logger.info(f"✅ Serving file: {file_path}")
    return FileResponse(
        path=file_path,
        media_type="audio/wav",
        filename=segment_filename
    )

@router.get("/download/{project_id}/{file_type}")
async def download_file(project_id: str, file_type: str):
    """ファイルダウンロード"""
    logger.info(f"📁 General download request: project={project_id}, type={file_type}")
    
    file_mapping = {
        "script": "script.yaml",
        "audio": "audio_combined.wav",  # 統合音声ファイルへ変更
        "subtitle": "subtitle.srt",
        "subtitle-vtt": "subtitle.vtt",
        "summary": "summary.txt",
        "summary-yaml": "summary.yaml",
        "content": "scraped_content.txt",
        "voice-prompt": "voice_prompt.yaml",
        "audio-info": "audio_files_info.yaml"  # 音声ファイル情報追加
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

@router.get("/audio-files/{project_id}")
async def get_audio_files_list(project_id: str):
    """プロジェクトの音声ファイル一覧取得"""
    try:
        # 音声ファイル情報を読み込み
        info_path = file_manager.get_file_path(project_id, "audio_files_info.yaml")
        
        if not os.path.exists(info_path):
            raise HTTPException(status_code=404, detail="Audio files info not found")
        
        with open(info_path, 'r', encoding='utf-8') as f:
            import yaml
            audio_files_info = yaml.safe_load(f)
        
        # 各ファイルの存在確認
        for file_info in audio_files_info:
            file_path = file_manager.get_file_path(project_id, file_info["filename"])
            file_info["exists"] = os.path.exists(file_path)
            file_info["download_url"] = f"/api/generate/download/{project_id}/segments/{file_info['filename']}"
        
        return {
            "project_id": project_id,
            "audio_files": audio_files_info,
            "total_files": len(audio_files_info),
            "combined_audio_url": f"/api/generate/download/{project_id}/audio"
        }
        
    except Exception as e:
        logger.error(f"Failed to get audio files list: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get audio files list")
