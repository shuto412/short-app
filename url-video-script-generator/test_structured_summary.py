#!/usr/bin/env python3
"""
構造化要約機能のテストスクリプト
"""

import asyncio
import sys
import os

# パス追加（url-video-script-generatorディレクトリ内で実行想定）
sys.path.append('backend')

async def test_structured_summary():
    """構造化要約生成のテスト"""
    print("🧪 構造化要約機能のテストを開始...")
    
    try:
        from app.modules.summarizer import ClaudeClient
        
        # テストデータ（現在のsummary.txtの内容）
        test_content = """Xlite CrazyLight Gaming Mouse Color: Jet Black - ¥16,940 JPYUyuni White - ¥16,940 JPY カートに追加する Dimension Same Size as the Xlite Size 1Length: 4.55in (115.6mm)Width: 2.5in (63.4mm)Height: 1.6in (40.7mm)Weight: ±41g (1.45oz) with dot skates / ±43g (1.52oz) with regular skates w/o cable Benefits 驚異的な軽さ41gで、手の疲労を軽減し、スピードを向上人間工学に基づいた右利き用形状により、快適な使用感を実現し、さまざまな握り方をサポート右利き用の手のひらグリップに最適化されたボディデザインは、長時間のゲームプレイ中にも優れた快適性と精密な操作性を提供XS-1フラッグシップセンサーを搭載し、正確なトラッキングと信頼性の高いパフォーマンスを提供最大8K（8000Hz）のポーリングレートに対応し、シームレスで..."""
        
        # Claude clientの初期化
        claude_client = ClaudeClient()
        print("✅ Claude clientの初期化成功")
        
        # 構造化要約の生成
        print("📝 構造化要約を生成中...")
        result = await claude_client.create_structured_summary(test_content)
        
        # 結果の確認
        print("📋 生成された構造化要約:")
        print(f"製品名: {result.get('product_name', 'なし')}")
        print(f"価格: {result.get('price', 'なし')}")
        print(f"製品詳細: {result.get('specifications', {})}")
        print(f"製品説明: {result.get('description', 'なし')[:100]}...")
        
        # 必須フィールドの存在確認
        required_fields = ['product_name', 'price', 'specifications', 'description']
        missing_fields = [field for field in required_fields if field not in result]
        
        if missing_fields:
            print(f"❌ 不足フィールド: {missing_fields}")
            return False
        else:
            print("✅ 全ての必須フィールドが存在")
        
        # specifications内の構造確認
        specs = result.get('specifications', {})
        if isinstance(specs, dict):
            print("✅ specifications が辞書形式で正しく構造化されている")
        else:
            print("❌ specifications の構造が不正")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ テスト失敗: {str(e)}")
        return False

async def test_yaml_output():
    """YAML出力のテスト"""
    print("\n🧪 YAML出力機能のテストを開始...")
    
    try:
        from app.modules.file_manager import FileManager
        import yaml
        from datetime import datetime
        
        # テストデータ
        test_data = {
            "metadata": {
                "project_id": "test-project-001",
                "url": "https://example.com/test",
                "generated_at": datetime.now().isoformat(),
                "content_length": 1000
            },
            "product_info": {
                "product_name": "Xlite CrazyLight Gaming Mouse",
                "price": "¥16,940 JPY",
                "specifications": {
                    "size": "Size 1",
                    "weight": "±41g (1.45oz)",
                    "dimensions": {
                        "length": "4.55in (115.6mm)",
                        "width": "2.5in (63.4mm)",
                        "height": "1.6in (40.7mm)"
                    }
                },
                "description": "驚異的な軽さ41gで、手の疲労を軽減し、スピードを向上"
            }
        }
        
        # ファイル管理の初期化
        file_manager = FileManager()
        test_project_id = "test-yaml-output"
        
        # YAML保存テスト
        print("💾 YAMLファイル保存テスト...")
        await file_manager.save_file(test_project_id, "test_summary.yaml", test_data)
        print("✅ YAML保存成功")
        
        # YAML読み込みテスト
        print("📖 YAMLファイル読み込みテスト...")
        loaded_data = await file_manager.read_file(test_project_id, "test_summary.yaml")
        print("✅ YAML読み込み成功")
        
        # データ整合性確認
        if loaded_data == test_data:
            print("✅ 保存・読み込みデータの整合性確認成功")
        else:
            print("❌ データの整合性に問題あり")
            return False
        
        # クリーンアップ
        file_manager.delete_project(test_project_id)
        print("🧹 テストファイル削除完了")
        
        return True
        
    except Exception as e:
        print(f"❌ YAML出力テスト失敗: {str(e)}")
        return False

async def main():
    """メインテスト関数"""
    print("=" * 50)
    print("🚀 URL動画台本生成システム - 構造化要約機能テスト")
    print("=" * 50)
    
    # テスト1: 構造化要約生成
    test1_result = await test_structured_summary()
    
    # テスト2: YAML出力
    test2_result = await test_yaml_output()
    
    # 結果サマリー
    print("\n" + "=" * 50)
    print("📊 テスト結果サマリー")
    print("=" * 50)
    print(f"構造化要約生成テスト: {'✅ 成功' if test1_result else '❌ 失敗'}")
    print(f"YAML出力テスト: {'✅ 成功' if test2_result else '❌ 失敗'}")
    
    if test1_result and test2_result:
        print("\n🎉 全テスト成功！実装完了です。")
        # 成功の音を鳴らす（macOS）
        os.system("afplay /System/Library/Sounds/Glass.aiff 2>/dev/null || echo '🔔 テスト完了'")
    else:
        print("\n⚠️  一部テストが失敗しました。確認が必要です。")

if __name__ == "__main__":
    asyncio.run(main()) 