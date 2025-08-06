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

    # 必要に応じて各段階のメソッドを追加