#!/usr/bin/env python3
"""
直接APIエンドポイントでのデバッグテスト
"""

import asyncio
import sys
import os

# パス追加
sys.path.append('url-video-script-generator/backend')

async def debug_api_generation():
    """API処理を直接デバッグ"""
    print("🔍 API生成処理直接デバッグ...")
    
    try:
        from app.modules.scraper import Scraper
        from app.modules.summarizer import ClaudeClient
        from app.modules.file_manager import FileManager
        from app.models.project import Project
        from datetime import datetime
        import uuid
        
        # 実際のAPIプロセス再現
        project_id = str(uuid.uuid4())
        test_url = "https://www.finalmouse.com/products/ninja-tenz"
        
        print(f"📝 プロジェクトID: {project_id[:8]}...")
        
        # モジュール初期化
        scraper = Scraper()
        file_manager = FileManager()
        
        try:
            claude_client = ClaudeClient()
            print("✅ Claude client初期化成功")
        except Exception as e:
            print(f"❌ Claude client初期化失敗: {str(e)}")
            return False
        
        # 1. スクレイピング
        print("🕷️ スクレイピング開始...")
        scraped_content = await scraper.scrape(test_url)
        await file_manager.save_file(project_id, "scraped_content.txt", scraped_content)
        print(f"✅ スクレイピング完了: {len(scraped_content)} characters")
        
        # 2. 構造化要約生成（API処理と同じロジック）
        print("📝 構造化要約生成開始...")
        try:
            # 構造化要約を生成
            structured_summary = await claude_client.create_structured_summary(scraped_content)
            print("✅ 構造化要約生成成功")
            
            # メタデータを追加
            summary_data = {
                "metadata": {
                    "project_id": project_id,
                    "url": test_url,
                    "generated_at": datetime.now().isoformat(),
                    "content_length": len(scraped_content)
                },
                "product_info": structured_summary
            }
            
            # YAMLファイルとして保存
            await file_manager.save_file(project_id, "summary.yaml", summary_data)
            print("✅ summary.yaml保存成功")
            
            # 後方互換性のため、従来のテキスト要約も生成・保存
            text_summary = await claude_client.summarize(scraped_content)
            await file_manager.save_file(project_id, "summary.txt", text_summary)
            print("✅ summary.txt保存成功")
            
        except Exception as e:
            print(f"❌ 構造化要約生成失敗: {str(e)}")
            import traceback
            print("詳細エラー:")
            traceback.print_exc()
            return False
        
        # 3. 結果確認
        print("\n📁 生成ファイル確認:")
        files = file_manager.list_project_files(project_id)
        for file in sorted(files):
            print(f"  - {file}")
        
        # summary.yamlの存在と内容確認
        if "summary.yaml" in files:
            yaml_content = await file_manager.read_file(project_id, "summary.yaml")
            print(f"\n✅ summary.yaml生成成功:")
            print(f"📋 製品名: {yaml_content['product_info']['product_name']}")
            print(f"📋 価格: {yaml_content['product_info']['price']}")
            
            # クリーンアップ
            file_manager.delete_project(project_id)
            print("🧹 テストプロジェクト削除完了")
            
            return True
        else:
            print("❌ summary.yamlが生成されていません")
            return False
        
    except Exception as e:
        print(f"❌ デバッグテスト失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """メイン実行関数"""
    print("=" * 60)
    print("🔍 API生成処理直接デバッグ")
    print("=" * 60)
    
    result = await debug_api_generation()
    
    print("\n" + "=" * 60)
    print("📊 デバッグ結果")
    print("=" * 60)
    
    if result:
        print("🎉 直接処理では正常に動作しています")
        print("   API サーバー処理に固有の問題があります")
    else:
        print("⚠️  直接処理でも問題が発生しています")

if __name__ == "__main__":
    asyncio.run(main()) 