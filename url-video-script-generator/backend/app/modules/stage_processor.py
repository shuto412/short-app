import logging
from app.modules.scraper import Scraper
from app.modules.summarizer import ClaudeClient
from app.modules.script_generator import ScriptGenerator
from app.modules.voice_generator import VoiceGenerator
from app.modules.subtitle_generator import SubtitleGenerator
from app.modules.file_manager import FileManager
from app.models.project import ProjectStage

logger = logging.getLogger(__name__)

class StageProcessor:
    def __init__(self):
        self.scraper = Scraper()
        try:
            self.claude_client = ClaudeClient()
        except Exception as e:
            logger.warning(f"Claude client initialization failed: {e}")
            self.claude_client = None
        self.script_generator = ScriptGenerator(self.claude_client)
        self.voice_generator = VoiceGenerator()
        self.subtitle_generator = SubtitleGenerator()
        self.file_manager = FileManager()

    async def process_stage_scraping(self, project_id: str, url: str) -> dict:
        """段階1: スクレイピング"""
        try:
            logger.info(f"[Stage] Scraping start: {project_id}")
            content = await self.scraper.scrape(url)
            await self.file_manager.save_file(project_id, "scraped_content.txt", content)
            logger.info(f"[Stage] Scraping done: {project_id}")
            return {"success": True}
        except Exception as e:
            logger.error(f"[Stage] Scraping failed: {project_id} - {e}")
            return {"success": False, "message": str(e)}

    async def process_stage_summary(self, project_id: str) -> dict:
        """段階2: 要約生成 (テキスト + 構造化YAMLフォールバック)"""
        try:
            logger.info(f"[Stage] Summary generation start: {project_id}")
            scraped_content = await self.file_manager.read_file(project_id, "scraped_content.txt")

            # テキスト要約
            try:
                if self.claude_client:
                    text_summary = await self.claude_client.summarize(scraped_content)
                else:
                    # 簡易フォールバック
                    text_summary = scraped_content[:500] + "..." if len(scraped_content) > 500 else scraped_content
            except Exception as e:
                logger.warning(f"[Stage] Text summary failed: {e}")
                text_summary = scraped_content[:500] + "..." if len(scraped_content) > 500 else scraped_content
            await self.file_manager.save_file(project_id, "summary.txt", text_summary)

            # 構造化要約
            summary_yaml = None
            if self.claude_client:
                try:
                    structured = await self.claude_client.create_structured_summary(scraped_content)
                    summary_yaml = {
                        "metadata": {
                            "project_id": project_id,
                        },
                        "product_info": structured,
                    }
                except Exception as e:
                    logger.warning(f"[Stage] Structured summary failed: {e}")

            if summary_yaml is None:
                # フォールバックYAML
                summary_yaml = {
                    "metadata": {"project_id": project_id, "fallback": True},
                    "product_info": {
                        "description": scraped_content[:200] + "..." if len(scraped_content) > 200 else scraped_content
                    },
                }
            await self.file_manager.save_file(project_id, "summary.yaml", summary_yaml)

            logger.info(f"[Stage] Summary generation done: {project_id}")
            return {"success": True}
        except Exception as e:
            logger.error(f"[Stage] Summary generation failed: {project_id} - {e}")
            return {"success": False, "message": str(e)}

    async def process_stage_script_generation(self, project_id: str, scenario_type: str) -> dict:
        """段階3: 台本生成"""
        try:
            logger.info(f"[Stage] Script generation start: {project_id}")
            try:
                summary_text = await self.file_manager.read_file(project_id, "summary.txt")
            except Exception:
                # フォールバック: scraped_contentから作成
                scraped_content = await self.file_manager.read_file(project_id, "scraped_content.txt")
                summary_text = scraped_content[:500] + "..." if len(scraped_content) > 500 else scraped_content

            script = await self.script_generator.generate(summary_text, scenario_type)
            # メタデータに project_id を付与
            if "metadata" in script and isinstance(script["metadata"], dict):
                script["metadata"]["project_id"] = project_id
            else:
                script["metadata"] = {"project_id": project_id}

            await self.file_manager.save_file(project_id, "script.yaml", script)
            logger.info(f"[Stage] Script generation done: {project_id}")
            return {"success": True}
        except Exception as e:
            logger.error(f"[Stage] Script generation failed: {project_id} - {e}")
            return {"success": False, "message": str(e)}

    async def process_stage_voice_prompt_creation(self, project_id: str, voice_actor_id: str, voice_speed: float = 1.0) -> dict:
        """段階4: 音声設定（プロンプト）作成"""
        try:
            logger.info(f"[Stage] Voice prompt creation start: {project_id}")
            # 入力ファイル確認
            await self.file_manager.read_file(project_id, "script.yaml")
            # スクリプト読み込み
            script = await self.file_manager.read_file(project_id, "script.yaml")
            prompt = self.voice_generator.create_voice_prompt(script, voice_actor_id, voice_speed or 1.0)
            await self.file_manager.save_file(project_id, "voice_prompt.yaml", prompt)
            logger.info(f"[Stage] Voice prompt creation done: {project_id}")
            return {"success": True}
        except Exception as e:
            logger.error(f"[Stage] Voice prompt creation failed: {project_id} - {e}")
            return {"success": False, "message": str(e)}

    async def process_stage_voice_generation(self, project_id: str) -> dict:
        """段階5: 音声・字幕生成"""
        try:
            logger.info(f"[Stage] Voice generation start: {project_id}")
            # 必要ファイル
            voice_prompt = await self.file_manager.read_file(project_id, "voice_prompt.yaml")

            # 個別音声生成
            audio_files = await self.voice_generator.generate_individual_files_from_script(voice_prompt)
            for f in audio_files:
                await self.file_manager.save_file(project_id, f["filename"], f["audio_data"])

            # 統合音声
            if audio_files:
                combined = self.voice_generator._combine_audio_segments([f["audio_data"] for f in audio_files])
                await self.file_manager.save_file(project_id, "audio_combined.wav", combined)

            # 情報保存
            audio_files_info = [
                {
                    "segment_id": f["segment_id"],
                    "filename": f["filename"],
                    "text": f["text"],
                    "duration": f["duration"],
                    "size_bytes": f.get("size_bytes"),
                    "error": f.get("error"),
                }
                for f in audio_files
            ]
            await self.file_manager.save_file(project_id, "audio_files_info.yaml", audio_files_info)

            # 字幕
            script = await self.file_manager.read_file(project_id, "script.yaml")
            subtitle_srt = self.subtitle_generator.generate_srt(script)
            await self.file_manager.save_file(project_id, "subtitle.srt", subtitle_srt)
            subtitle_vtt = self.subtitle_generator.generate_vtt(script)
            await self.file_manager.save_file(project_id, "subtitle.vtt", subtitle_vtt)

            logger.info(f"[Stage] Voice generation done: {project_id}")
            return {"success": True}
        except Exception as e:
            logger.error(f"[Stage] Voice generation failed: {project_id} - {e}")
            return {"success": False, "message": str(e)}