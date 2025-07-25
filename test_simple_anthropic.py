#!/usr/bin/env python3
"""
Simple Anthropic client test
"""

import sys
sys.path.append('.')

def test_anthropic():
    print("🔍 Anthropic client テスト開始...")
    
    try:
        import anthropic
        print(f"✅ Anthropic version: {anthropic.__version__}")
        
        from app.config import settings
        print(f"✅ API key configured: {'SET' if settings.CLAUDE_API_KEY and settings.CLAUDE_API_KEY != 'your_key_here' else 'NOT SET'}")
        
        # クライアント初期化テスト
        client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)
        print("✅ Anthropic client初期化成功")
        
        # 簡単なテストメッセージ
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=100,
            messages=[{"role": "user", "content": "Hello, say 'Test successful' in Japanese."}]
        )
        
        response = message.content[0].text
        print(f"✅ API呼び出し成功: {response}")
        
        return True
        
    except Exception as e:
        print(f"❌ エラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_anthropic() 