#!/usr/bin/env python3
"""
現在のプロジェクトデータでsummary.yaml再生成テスト
"""

import asyncio
import sys
import os
import yaml

# パス追加
sys.path.append('backend')

async def test_current_project_summary():
    """現在のプロジェクトデータでsummary.yamlを再生成"""
    print("🔄 現在のプロジェクトでsummary.yaml再生成テスト開始...")
    
    try:
        from app.modules.summarizer import ClaudeClient
        from app.modules.file_manager import FileManager
        from datetime import datetime
        
        # 実際に存在するプロジェクトID
        project_id = "0ac29b60-ac51-4a11-bc78-bcb98b33574f"
        
        # ファイル管理とClaude clientの初期化
        file_manager = FileManager()
        # DATA_DIRを正しく設定
        file_manager.base_dir = "../../DATA"
        
        claude_client = ClaudeClient()
        print("✅ ClaudeClient初期化成功")
        
        print(f"📖 プロジェクト {project_id} のスクレイピング内容を読み込み中...")
        
        # 実際のスクレイピング内容を読み込み
        scraped_content = await file_manager.read_file(project_id, "scraped_content.txt")
        print(f"✅ スクレイピング内容読み込み完了 ({len(scraped_content)} 文字)")
        print(f"📝 スクレイピング内容の一部: {scraped_content[:100]}...")
        
        # 構造化要約を生成
        print("🧠 Claude APIで構造化要約を生成中...")
        structured_summary = await claude_client.create_structured_summary(scraped_content)
        
        # 結果の詳細表示
        print("\n📋 生成された構造化要約の詳細:")
        print("=" * 60)
        print(f"製品名: {structured_summary.get('product_name', 'なし')}")
        print(f"価格: {structured_summary.get('price', 'なし')}")
        
        specs = structured_summary.get('specifications', {})
        print(f"\n📐 仕様:")
        print(f"  サイズ: {specs.get('size', 'なし')}")
        print(f"  重量: {specs.get('weight', 'なし')}")
        
        dimensions = specs.get('dimensions', {})
        print(f"  寸法:")
        print(f"    長さ: {dimensions.get('length', 'なし')}")
        print(f"    幅: {dimensions.get('width', 'なし')}")
        print(f"    高さ: {dimensions.get('height', 'なし')}")
        
        print(f"  素材: {specs.get('materials', 'なし')}")
        print(f"  機能: {specs.get('features', [])}")
        print(f"  その他: {specs.get('other', 'なし')}")
        
        description = structured_summary.get('description', 'なし')
        print(f"\n📝 製品説明: {description[:100]}...")
        
        # メタデータを追加して完全な summary.yaml データを作成
        summary_data = {
            "metadata": {
                "project_id": project_id,
                "url": "https://jp.pulsar.gg/collections/mice/products/x3-lhd-gaming-mouse",
                "generated_at": datetime.now().isoformat(),
                "content_length": len(scraped_content),
                "updated": True,
                "claude_api_working": True,
                "regenerated": True
            },
            "product_info": structured_summary
        }
        
        # 古いsummary.yamlと比較
        print("\n📊 改善前後の比較:")
        try:
            old_summary = await file_manager.read_file(project_id, "summary.yaml")
            old_product_info = old_summary.get("product_info", {})
            
            print("改善前:")
            print(f"  製品名: {old_product_info.get('product_name', 'なし')}")
            print(f"  価格: {old_product_info.get('price', 'なし')}")
            print(f"  重量: {old_product_info.get('specifications', {}).get('weight', 'なし')}")
            
            print("改善後:")
            print(f"  製品名: {structured_summary.get('product_name', 'なし')}")
            print(f"  価格: {structured_summary.get('price', 'なし')}")
            print(f"  重量: {specs.get('weight', 'なし')}")
            
        except Exception as e:
            print(f"⚠️  古いsummary.yamlの読み込みに失敗: {str(e)}")
        
        # 新しい summary.yaml を保存
        print(f"\n💾 新しいsummary.yamlを保存中...")
        await file_manager.save_file(project_id, "summary.yaml", summary_data)
        print("✅ summary.yaml を更新しました")
        
        return True
        
    except Exception as e:
        print(f"❌ テスト失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """メインテスト関数"""
    print("=" * 60)
    print("🚀 現在のプロジェクトでsummary.yaml再生成テスト")
    print("=" * 60)
    
    result = await test_current_project_summary()
    
    print("\n" + "=" * 60)
    print("📊 テスト結果")
    print("=" * 60)
    
    if result:
        print("🎉 summary.yaml再生成テスト成功！")
        # 成功の音を鳴らす（macOS）
        os.system("afplay /System/Library/Sounds/Glass.aiff 2>/dev/null || echo '🔔 テスト完了'")
    else:
        print("❌ summary.yaml再生成テストに失敗しました")

if __name__ == "__main__":
    asyncio.run(main()) 