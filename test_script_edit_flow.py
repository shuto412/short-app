#!/usr/bin/env python3
"""
シナリオ編集機能の動作確認テスト
"""
import asyncio
import aiohttp
import json
import sys
import os

# プロジェクトルートをパスに追加
sys.path.append(os.path.join(os.path.dirname(__file__), 'url-video-script-generator', 'backend'))

async def test_script_edit_flow():
    """シナリオ編集機能の動作確認"""
    
    base_url = "http://localhost:8080"
    
    print("🧪 シナリオ編集機能テスト開始")
    
    # 1. プロジェクト作成
    print("\n1️⃣ プロジェクト作成...")
    async with aiohttp.ClientSession() as session:
        project_data = {
            "url": "https://example.com",
            "scenario_type": "product_introduction",
            "options": {}
        }
        
        async with session.post(f"{base_url}/api/projects", json=project_data) as response:
            if response.status == 200:
                result = await response.json()
                project_id = result.get("project_id")
                print(f"✅ プロジェクト作成成功: {project_id}")
            else:
                print(f"❌ プロジェクト作成失敗: {response.status}")
                error_text = await response.text()
                print(f"エラー詳細: {error_text}")
                return
    
    # 2. スクレイピング実行
    print("\n2️⃣ スクレイピング実行...")
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{base_url}/api/stages/scraping?project_id={project_id}") as response:
            if response.status == 200:
                print("✅ スクレイピング開始成功")
            else:
                print(f"❌ スクレイピング開始失敗: {response.status}")
                error_text = await response.text()
                print(f"エラー詳細: {error_text}")
                return
    
    # スクレイピング完了まで待機
    print("⏳ スクレイピング完了まで待機...")
    await asyncio.sleep(10)  # 10秒待機
    
    # 3. 要約生成実行
    print("\n3️⃣ 要約生成実行...")
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{base_url}/api/stages/summary?project_id={project_id}") as response:
            if response.status == 200:
                print("✅ 要約生成開始成功")
            else:
                print(f"❌ 要約生成開始失敗: {response.status}")
                error_text = await response.text()
                print(f"エラー詳細: {error_text}")
                return
    
    # 要約生成完了まで待機
    print("⏳ 要約生成完了まで待機...")
    await asyncio.sleep(10)  # 10秒待機
    
    # 4. 台本生成処理開始
    print("\n4️⃣ 台本生成処理開始...")
    async with aiohttp.ClientSession() as session:
        generation_data = {
            "project_id": project_id,
            "scenario_type": "product_introduction"
        }
        
        async with session.post(f"{base_url}/api/stages/script", json=generation_data) as response:
            if response.status == 200:
                print("✅ 台本生成処理開始成功")
            else:
                print(f"❌ 台本生成処理開始失敗: {response.status}")
                error_text = await response.text()
                print(f"エラー詳細: {error_text}")
                return
    
    # 台本生成完了まで待機
    print("⏳ 台本生成完了まで待機...")
    await asyncio.sleep(10)  # 10秒待機
    
    # 5. 処理完了まで待機
    print("\n5️⃣ 処理完了まで待機...")
    max_wait = 60  # 最大60秒待機
    wait_count = 0
    
    async with aiohttp.ClientSession() as session:
        while wait_count < max_wait:
            async with session.get(f"{base_url}/api/projects/{project_id}/status") as response:
                if response.status == 200:
                    status_data = await response.json()
                    status = status_data.get("status")
                    print(f"📊 処理状況: {status}")
                    
                    if status == "completed":
                        print("✅ 処理完了")
                        break
                    elif status == "failed":
                        print("❌ 処理失敗")
                        return
                
            await asyncio.sleep(2)
            wait_count += 1
        
        if wait_count >= max_wait:
            print("⏰ タイムアウト: 処理が完了しませんでした")
            return
    
    # 6. 台本取得テスト
    print("\n6️⃣ 台本取得テスト...")
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{base_url}/api/script/{project_id}") as response:
            if response.status == 200:
                script_data = await response.json()
                print("✅ 台本取得成功")
                print(f"📝 台本タイトル: {script_data.get('script', {}).get('metadata', {}).get('title', 'N/A')}")
                print(f"🎬 シーン数: {len(script_data.get('script', {}).get('scenes', []))}")
            else:
                print(f"❌ 台本取得失敗: {response.status}")
                error_text = await response.text()
                print(f"エラー詳細: {error_text}")
                return
    
    # 7. 台本更新テスト
    print("\n7️⃣ 台本更新テスト...")
    async with aiohttp.ClientSession() as session:
        # 既存の台本データを取得
        async with session.get(f"{base_url}/api/script/{project_id}") as response:
            if response.status == 200:
                original_script = await response.json()
                script = original_script.get("script")
                
                if script and script.get("scenes"):
                    # 最初のシーンのテキストを更新
                    first_scene = script["scenes"][0]
                    first_scene["text"] = "テスト用に更新されたテキストです。"
                    first_scene["is_edited"] = True
                    
                    # 台本を更新
                    async with session.put(f"{base_url}/api/script/{project_id}", json=script) as update_response:
                        if update_response.status == 200:
                            print("✅ 台本更新成功")
                        else:
                            print(f"❌ 台本更新失敗: {update_response.status}")
                            error_text = await update_response.text()
                            print(f"エラー詳細: {error_text}")
                else:
                    print("❌ シーンが見つかりません")
            else:
                print("❌ 台本取得に失敗しました")
    
    print("\n🎉 シナリオ編集機能テスト完了")

if __name__ == "__main__":
    asyncio.run(test_script_edit_flow()) 