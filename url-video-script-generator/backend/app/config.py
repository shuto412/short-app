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
        
        # Claude API キーの設定チェック
        if not self.CLAUDE_API_KEY or self.CLAUDE_API_KEY == "your_claude_api_key_here":
            print("⚠️  Claude API キーが設定されていません！")
            print("📋 設定方法:")
            print("   1. backendディレクトリに .env ファイルを作成")
            print("   2. 以下の内容を追加:")
            print("      CLAUDE_API_KEY=your_actual_api_key")
            print("      NIJIVOICE_API_KEY=your_nijivoice_api_key")
            print("      DATA_DIR=../DATA")
            print("   3. バックエンドサーバーを再起動")
            print("💡 または環境変数として設定:")
            print("   export CLAUDE_API_KEY=your_actual_api_key")
    
settings = Settings()
