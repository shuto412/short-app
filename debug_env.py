#!/usr/bin/env python3
"""
環境変数読み込み問題のデバッグスクリプト
"""

import os
import sys

def debug_env_loading():
    print("🔍 環境変数読み込み問題のデバッグ")
    print("=" * 50)
    
    # 1. 現在の作業ディレクトリ確認
    print(f"📁 現在の作業ディレクトリ: {os.getcwd()}")
    
    # 2. .envファイルの存在確認
    possible_env_paths = [
        ".env",
        "backend/.env", 
        "url-video-script-generator/backend/.env",
        "../.env"
    ]
    
    print("\n🔍 .envファイルの存在確認:")
    env_file_found = None
    for path in possible_env_paths:
        if os.path.exists(path):
            print(f"  ✅ {path} - 存在")
            env_file_found = path
        else:
            print(f"  ❌ {path} - 存在しない")
    
    # 3. .envファイルの内容確認
    if env_file_found:
        print(f"\n📖 {env_file_found} の内容:")
        try:
            with open(env_file_found, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if line.strip():
                        # APIキーは一部隠してログ出力
                        if 'API_KEY' in line:
                            key_part = line.split('=')[0] if '=' in line else line
                            value_part = line.split('=')[1] if '=' in line and len(line.split('=')) > 1 else ''
                            masked_value = value_part[:5] + "*" * 20 + value_part[-5:] if len(value_part) > 10 else "設定あり"
                            print(f"    {i}: {key_part}={masked_value}")
                        else:
                            print(f"    {i}: {line}")
        except Exception as e:
            print(f"  ❌ ファイル読み込みエラー: {str(e)}")
    
    # 4. python-dotenvを使用して明示的に読み込み
    print(f"\n🔄 python-dotenvで明示的に読み込み:")
    try:
        from dotenv import load_dotenv
        
        # 見つかった.envファイルを明示的に指定
        if env_file_found:
            result = load_dotenv(env_file_found, override=True)
            print(f"  ✅ load_dotenv('{env_file_found}') = {result}")
        else:
            result = load_dotenv()
            print(f"  ⚠️  load_dotenv() = {result} (.envファイルが見つからない)")
            
    except Exception as e:
        print(f"  ❌ load_dotenvエラー: {str(e)}")
    
    # 5. 環境変数の実際の値確認
    print(f"\n🔍 環境変数の実際の値:")
    env_vars = ['CLAUDE_API_KEY', 'NIJIVOICE_API_KEY', 'DATA_DIR', 'BACKEND_PORT']
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            if 'API_KEY' in var:
                masked_value = value[:5] + "*" * 20 + value[-5:] if len(value) > 10 else "設定あり"
                print(f"  ✅ {var} = {masked_value}")
            else:
                print(f"  ✅ {var} = {value}")
        else:
            print(f"  ❌ {var} = 未設定")
    
    # 6. app.configからの読み込みテスト
    print(f"\n🔍 app.configからの設定読み込みテスト:")
    try:
        # パスを追加
        if 'url-video-script-generator/backend' not in sys.path:
            sys.path.append('url-video-script-generator/backend')
        
        from app.config import settings
        
        # 設定値確認
        api_key = settings.CLAUDE_API_KEY
        if api_key:
            if api_key == "your_key_here" or api_key == "your_claude_api_key_here":
                print(f"  ⚠️  CLAUDE_API_KEY = デフォルト値（未設定）")
            else:
                masked_key = api_key[:5] + "*" * 20 + api_key[-5:] if len(api_key) > 10 else "設定あり"
                print(f"  ✅ CLAUDE_API_KEY = {masked_key}")
        else:
            print(f"  ❌ CLAUDE_API_KEY = None")
            
    except Exception as e:
        print(f"  ❌ app.config読み込みエラー: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # 7. Claude client初期化テスト
    print(f"\n🔍 Claude client初期化テスト:")
    try:
        from app.modules.summarizer import ClaudeClient
        claude_client = ClaudeClient()
        print(f"  ✅ ClaudeClient初期化成功")
    except Exception as e:
        print(f"  ❌ ClaudeClient初期化失敗: {str(e)}")

if __name__ == "__main__":
    debug_env_loading() 