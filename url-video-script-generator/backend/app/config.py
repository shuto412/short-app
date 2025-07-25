import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    def __init__(self):
        self.CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
        self.NIJIVOICE_API_KEY = os.getenv("NIJIVOICE_API_KEY")
        self.DATA_DIR = os.getenv("DATA_DIR", "../DATA")
        self.MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
        self.BACKEND_PORT = int(os.getenv("BACKEND_PORT", 8080))
    
settings = Settings()
