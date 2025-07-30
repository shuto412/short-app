#!/usr/bin/env python3
"""
Nijivoice API 設定デバッグテストスクリプト
"""

import asyncio
import sys
import os
from pathlib import Path

# パス追加
sys.path.append('url-video-script-generator/backend')

async def test_voice_generator_config():
    """VoiceGenerator設定の詳細テスト"""
    print("🔧 Nijivoice API 設定テスト開始...")
    print("=" * 60)
    
    try:
        # 設定読み込み
        from app.config import settings
        from app.modules.voice_generator import VoiceGenerator
        
        print(f"\n📊 設定情報:")
        print(f"  - 現在の作業ディレクトリ: {os.getcwd()}")
        print(f"  - DATA_DIR: {settings.DATA_DIR}")
        print(f"  - BACKEND_PORT: {settings.BACKEND_PORT}")
        
        # VoiceGenerator初期化テスト
        print(f"\n🎙️ VoiceGenerator初期化テスト:")
        voice_gen = VoiceGenerator()
        
        # ボイスアクター取得テスト
        print(f"\n🎤 ボイスアクター取得テスト:")
        voice_actors = await voice_gen.get_voice_actors()
        print(f"  ✅ 取得したボイスアクター数: {len(voice_actors)}")
        for i, actor in enumerate(voice_actors[:3]):  # 最初の3個のみ表示
            print(f"    {i+1}. {actor.get('name', 'Unknown')} (ID: {actor.get('id', 'Unknown')})")
        
        # 音声生成テスト
        print(f"\n🎵 音声生成テスト:")
        test_text = "これはテスト音声です。"
        if voice_actors:
            voice_actor_id = voice_actors[0]['id']
            audio_data = await voice_gen.generate(voice_actor_id, test_text)
            print(f"  ✅ 音声データ生成成功: {len(audio_data)} bytes")
            print(f"  📊 使用したボイスアクター: {voice_actor_id}")
            print(f"  📝 生成したテキスト: {test_text}")
        else:
            print(f"  ❌ ボイスアクターが取得できませんでした")
        
        print(f"\n✅ 全てのテストが完了しました")
        
    except Exception as e:
        print(f"❌ テスト中にエラーが発生しました: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_voice_generator_config()) 