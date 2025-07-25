#!/usr/bin/env python3
"""
実際のプロジェクトデータで構造化要約生成をテストするスクリプト
"""

import asyncio
import sys
import os

# パス追加
sys.path.append('backend')

async def test_actual_project():
    """実際のプロジェクトデータで構造化要約をテスト"""
    print("🧪 実際のプロジェクトデータでのテストを開始...")
    
    try:
        from app.modules.summarizer import ClaudeClient
        from app.modules.file_manager import FileManager
        from datetime import datetime
        
        # 実際のプロジェクトデータを使用
        project_id = "0564458c-28a5-40bb-9a92-d2796fc684e1"
        
        file_manager = FileManager()
        claude_client = ClaudeClient()
        
        # 既存のsummary.txtを読み込み
        print(f"📖 プロジェクト {project_id} のsummary.txtを読み込み中...")
        try:
            original_summary = await file_manager.read_file(project_id, "summary.txt")
            print(f"✅ 既存要約読み込み成功 ({len(original_summary)} 文字)")
            print(f"📋 既存要約の一部: {original_summary[:100]}...")
        except Exception as e:
            print(f"❌ 既存要約読み込み失敗: {str(e)}")
            return False
        
        # 構造化要約を生成
        print("🔧 構造化要約を生成中...")
        structured_summary = await claude_client.create_structured_summary(original_summary)
        
        # メタデータを追加
        summary_data = {
            "metadata": {
                "project_id": project_id,
                "url": "https://example.com/gaming-mouse",
                "generated_at": datetime.now().isoformat(),
                "content_length": len(original_summary),
                "source": "existing_summary_upgrade"
            },
            "product_info": structured_summary
        }
        
        # 構造化要約をYAMLとして保存
        print("💾 構造化要約をsummary.yamlとして保存中...")
        await file_manager.save_file(project_id, "summary.yaml", summary_data)
        print("✅ summary.yaml保存成功")
        
        # 結果を表示
        print("\n📋 生成された構造化要約:")
        print(f"製品名: {structured_summary.get('product_name')}")
        print(f"価格: {structured_summary.get('price')}")
        print("仕様詳細:")
        specs = structured_summary.get('specifications', {})
        for key, value in specs.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for sub_key, sub_value in value.items():
                    print(f"    {sub_key}: {sub_value}")
            else:
                print(f"  {key}: {value}")
        print(f"説明: {structured_summary.get('description')[:100]}...")
        
        # ファイル一覧確認
        print("\n📁 プロジェクトファイル一覧:")
        files = file_manager.list_project_files(project_id)
        for file in sorted(files):
            print(f"  - {file}")
        
        # 新しいsummary.yamlが存在することを確認
        if "summary.yaml" in files:
            print("✅ summary.yamlが正常に作成されました")
        else:
            print("❌ summary.yamlの作成に失敗")
            return False
        
        # YAML内容確認
        print("\n🔍 生成されたYAMLファイル内容確認:")
        loaded_yaml = await file_manager.read_file(project_id, "summary.yaml")
        print(f"メタデータ - プロジェクトID: {loaded_yaml['metadata']['project_id']}")
        print(f"メタデータ - 生成日時: {loaded_yaml['metadata']['generated_at']}")
        print(f"製品情報 - 製品名: {loaded_yaml['product_info']['product_name']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 実際プロジェクトテスト失敗: {str(e)}")
        return False

async def main():
    """メインテスト関数"""
    print("=" * 60)
    print("🚀 実際のプロジェクトデータでの構造化要約機能テスト")
    print("=" * 60)
    
    result = await test_actual_project()
    
    print("\n" + "=" * 60)
    print("📊 テスト結果")
    print("=" * 60)
    
    if result:
        print("🎉 実際のプロジェクトデータでのテスト成功！")
        print("   既存のsummary.txtから構造化されたsummary.yamlが正常に生成されました。")
        # 成功の音を鳴らす
        os.system("afplay /System/Library/Sounds/Hero.aiff 2>/dev/null || echo '🔔 テスト完了'")
    else:
        print("⚠️  テストが失敗しました。")

if __name__ == "__main__":
    asyncio.run(main()) 