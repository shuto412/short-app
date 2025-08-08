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