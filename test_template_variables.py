#!/usr/bin/env python3
"""
テンプレート変数置換機能のテスト
"""

import sys
import os
import yaml

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.join(os.path.dirname(__file__), 'url-video-script-generator', 'backend'))

from app.modules.script_generator import ScriptGenerator

def test_template_variable_replacement():
    """テンプレート変数置換機能のテスト"""
    
    # テスト用のsummary.yamlデータ
    test_summary = """
metadata:
  project_id: test-123
product_info:
  description: 競技eスポーツに最適化された軽量41gのゲーミングマウス
  price:
    - 'Jet Black: 売り切れ'
    - 'Uyuni White: ¥16,940 JPY'
  product_name: Xlite CrazyLight Gaming Mouse
  specifications:
    dimensions:
      height: 1.61in (40.7mm)
      length: 4.55in (115.6mm)
      width: 2.5in (63.5mm)
    features:
      - 驚異的な軽さ41g
      - 人間工学に基づいた右利き用形状
      - XS-1フラッグシップセンサー搭載
    weight: ±41g (1.45oz)
"""
    
    # テスト用のテンプレート
    test_template = {
        "name": "ゲーミングマウス製品紹介",
        "description": "製品の特徴と利点を効果的に紹介するシナリオ",
        "structure": [
            {
                "section": "opening",
                "name": "オープニング",
                "duration_ratio": 0.15,
                "description": "こんにちは！マウスログです、今回は{product_name}をご紹介します。{product_description}を簡単に説明しますね。"
            },
            {
                "section": "solution",
                "name": "紹介するゲーミングマウスのメリットで解決",
                "duration_ratio": 0.45,
                "description": "{product_name}の主要機能である{features}について詳しく説明し、{weight}の軽さと{dimensions}のサイズ感、そして{price}の価格設定についても触れます。"
            }
        ],
        "voice_settings": {
            "emotion": "confident",
            "speed": 1.0,
            "pitch": 1.0,
            "volume": 1.0
        }
    }
    
    try:
        # ScriptGeneratorのインスタンスを作成（ClaudeクライアントはNone）
        generator = ScriptGenerator(claude_client=None)
        
        # 変数置換をテスト
        summary_data = generator._parse_summary_yaml(test_summary)
        print("=== 解析されたsummary.yaml ===")
        print(f"product_name: {summary_data.get('product_info', {}).get('product_name')}")
        print(f"product_description: {summary_data.get('product_info', {}).get('description')}")
        print(f"price: {summary_data.get('product_info', {}).get('price')}")
        print(f"features: {summary_data.get('product_info', {}).get('specifications', {}).get('features')}")
        print(f"weight: {summary_data.get('product_info', {}).get('specifications', {}).get('weight')}")
        print(f"dimensions: {summary_data.get('product_info', {}).get('specifications', {}).get('dimensions')}")
        print()
        
        # テンプレート変数置換をテスト
        replaced_template = generator._replace_template_variables(test_template, summary_data)
        
        print("=== 変数置換後のテンプレート ===")
        for section in replaced_template['structure']:
            print(f"セクション: {section['name']}")
            print(f"説明: {section['description']}")
            print()
        
        # 特定の変数が正しく置換されているかチェック
        opening_desc = replaced_template['structure'][0]['description']
        solution_desc = replaced_template['structure'][1]['description']
        
        print("=== 置換結果の検証 ===")
        print(f"opening説明にproduct_nameが含まれている: {'Xlite CrazyLight Gaming Mouse' in opening_desc}")
        print(f"opening説明にproduct_descriptionが含まれている: {'競技eスポーツに最適化された軽量41gのゲーミングマウス' in opening_desc}")
        print(f"solution説明にfeaturesが含まれている: {'驚異的な軽さ41g' in solution_desc}")
        print(f"solution説明にweightが含まれている: {'±41g (1.45oz)' in solution_desc}")
        print(f"solution説明にpriceが含まれている: {'¥16,940 JPY' in solution_desc}")
        
        print("\n✅ テンプレート変数置換機能のテストが完了しました！")
        
    except Exception as e:
        print(f"❌ テスト中にエラーが発生しました: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_template_variable_replacement()
