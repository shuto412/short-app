#!/usr/bin/env python3
"""
既存のsummary.txtを直接使って構造化要約生成をテストするスクリプト
"""

import asyncio
import sys
import os

# パス追加
sys.path.append('url-video-script-generator/backend')

async def test_direct_summary():
    """既存のsummary.txtファイルを直接使って構造化要約をテスト"""
    print("🧪 既存summary.txtファイルでの構造化要約テストを開始...")
    
    try:
        from app.modules.summarizer import ClaudeClient
        from datetime import datetime
        import yaml
        
        # 既存のsummary.txtを直接読み込み
        summary_file_path = "url-video-script-generator/DATA/0564458c-28a5-40bb-9a92-d2796fc684e1/summary.txt"
        
        print(f"📖 summary.txtファイルを読み込み中: {summary_file_path}")
        
        with open(summary_file_path, 'r', encoding='utf-8') as f:
            original_summary = f.read()
        
        print(f"✅ ファイル読み込み成功 ({len(original_summary)} 文字)")
        print(f"📋 内容の一部: {original_summary[:100]}...")
        
        # Claude clientの初期化
        claude_client = ClaudeClient()
        print("✅ Claude clientの初期化成功")
        
        # 構造化要約を生成
        print("🔧 構造化要約を生成中...")
        structured_summary = await claude_client.create_structured_summary(original_summary)
        
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
        print(f"説明: {structured_summary.get('description')[:150]}...")
        
        # メタデータを追加してYAML構造を作成
        summary_data = {
            "metadata": {
                "project_id": "0564458c-28a5-40bb-9a92-d2796fc684e1",
                "url": "https://example.com/gaming-mouse",
                "generated_at": datetime.now().isoformat(),
                "content_length": len(original_summary),
                "source": "existing_summary_upgrade"
            },
            "product_info": structured_summary
        }
        
        # 新しいsummary.yamlファイルとして保存
        output_path = "url-video-script-generator/DATA/0564458c-28a5-40bb-9a92-d2796fc684e1/summary.yaml"
        print(f"\n💾 YAMLファイルとして保存中: {output_path}")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(summary_data, f, allow_unicode=True, default_flow_style=False)
        
        print("✅ summary.yaml保存成功")
        
        # 保存したファイルを確認
        print("\n🔍 保存されたYAMLファイル内容確認:")
        with open(output_path, 'r', encoding='utf-8') as f:
            saved_content = f.read()
        
        print(f"ファイルサイズ: {len(saved_content)} 文字")
        print("内容の一部:")
        print(saved_content[:300] + "...")
        
        return True
        
    except Exception as e:
        print(f"❌ テスト失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """メインテスト関数"""
    print("=" * 60)
    print("🚀 既存summary.txtから構造化YAML生成テスト")
    print("=" * 60)
    
    result = await test_direct_summary()
    
    print("\n" + "=" * 60)
    print("📊 テスト結果")
    print("=" * 60)
    
    if result:
        print("🎉 既存summary.txtからのYAML生成テスト成功！")
        print("   - 製品情報が構造化された形式で抽出されました")
        print("   - summary.yamlファイルが正常に生成されました")
        print("   - システムの改良が完了しました！")
        # 成功の音を鳴らす
        os.system("afplay /System/Library/Sounds/Glass.aiff 2>/dev/null || echo '🔔 完了音'")
    else:
        print("⚠️  テストが失敗しました。")

if __name__ == "__main__":
    asyncio.run(main()) 