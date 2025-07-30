import os
from dotenv import load_dotenv
from pathlib import Path

# .envファイルの読み込み（複数パスを試行）
env_paths = [
    ".env",                           # カレントディレクトリ
    "backend/.env",                   # backendディレクトリ
    "../.env",                        # 親ディレクトリ
    Path(__file__).parent.parent / ".env",  # このファイルの親の親
]

env_loaded = False
for env_path in env_paths:
    if Path(env_path).exists():
        load_dotenv(env_path)
        print(f"📁 .envファイル読み込み成功: {env_path}")
        env_loaded = True
        break

if not env_loaded:
    print("⚠️  .envファイルが見つかりませんでした")
    print(f"📍 現在の作業ディレクトリ: {os.getcwd()}")
    print("🔍 検索したパス:")
    for path in env_paths:
        print(f"   - {path} ({'存在' if Path(path).exists() else '存在しない'})")

# 環境変数の実際の読み込み状況を確認
print("🔧 環境変数読み込み確認:")
print(f"  NIJIVOICE_API_KEY: {'設定済み' if os.getenv('NIJIVOICE_API_KEY') else 'None'}")
print(f"  CLAUDE_API_KEY: {'設定済み' if os.getenv('CLAUDE_API_KEY') else 'None'}")
if os.getenv('NIJIVOICE_API_KEY'):
    print(f"  NIJIVOICE_API_KEY長さ: {len(os.getenv('NIJIVOICE_API_KEY'))}")
    print(f"  NIJIVOICE_API_KEY先頭: {os.getenv('NIJIVOICE_API_KEY')[:8]}...")

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
        
        # Nijivoice API キーの設定チェック
        print(f"\n🔍 Nijivoice API キー設定状況:")
        if self.NIJIVOICE_API_KEY:
            if self.NIJIVOICE_API_KEY == "your_key_here" or self.NIJIVOICE_API_KEY == "your_nijivoice_api_key":
                print("  ⚠️  Nijivoice API キーがデフォルト値です")
            else:
                # APIキーの最初と最後の数文字のみを表示
                masked_key = f"{self.NIJIVOICE_API_KEY[:8]}...{self.NIJIVOICE_API_KEY[-4:]}" if len(self.NIJIVOICE_API_KEY) > 12 else "設定済み"
                print(f"  ✅ Nijivoice API キー: {masked_key}")
                print(f"  📏 キー長: {len(self.NIJIVOICE_API_KEY)} 文字")
        else:
            print("  ❌ Nijivoice API キーが設定されていません")
    
settings = Settings()
