#!/usr/bin/env python3
"""
修正されたテンプレート変数置換機能のテスト
"""

import sys
import os

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.join(os.path.dirname(__file__), 'url-video-script-generator', 'backend'))

from app.modules.script_generator import ScriptGenerator

def test_fixed_template_generation():
    """修正されたテンプレート生成機能をテスト"""
    
    try:
        # 実際のsummary.yamlファイルのパス
        summary_file_path = 'url-video-script-generator/DATA/13cc646a-cff6-415b-b472-18cef5225376/summary.yaml'
        
        # summary.yamlファイルを読み込み
        with open(summary_file_path, 'r', encoding='utf-8') as f:
            summary_content = f.read()
        
        # ScriptGeneratorのインスタンスを作成
        generator = ScriptGenerator(claude_client=None)
        
        # summary.yamlを解析
        summary_data = generator._parse_summary_yaml(summary_content)
        print('=== 実際のsummary.yamlから抽出されたデータ ===')
        print(f'product_name: {summary_data.get("product_info", {}).get("product_name")}')
        print(f'product_description: {summary_data.get("product_info", {}).get("description")}')
        print(f'price: {summary_data.get("product_info", {}).get("price")}')
        print(f'features: {summary_data.get("product_info", {}).get("specifications", {}).get("features")}')
        print(f'weight: {summary_data.get("product_info", {}).get("specifications", {}).get("weight")}')
        
        # テンプレートを読み込み
        template = generator._load_template('mouselog_temp1')
        print('\n=== 元のテンプレート ===')
        for section in template['structure']:
            print(f'{section["name"]}: {section["description"]}')
        
        # 変数置換を実行
        replaced_template = generator._replace_template_variables(template, summary_data)
        print('\n=== 変数置換後のテンプレート ===')
        for section in replaced_template['structure']:
            print(f'{section["name"]}: {section["description"]}')
        
        # プロンプト生成をテスト
        prompt = generator._create_generation_prompt(summary_content, replaced_template, 60)
        print('\n=== 生成されたプロンプト（一部） ===')
        print(prompt[:1000] + '...' if len(prompt) > 1000 else prompt)
        
        # ひらがな変換のテスト
        sample_text = replaced_template['structure'][0]['description']
        hiragana_text = generator._convert_to_hiragana(sample_text)
        print('\n=== ひらがな変換テスト ===')
        print(f'元のテキスト: {sample_text}')
        print(f'ひらがな版: {hiragana_text}')
        
        print('\n✅ 修正されたテンプレート変数置換機能のテストが完了しました！')
        
    except Exception as e:
        print(f'❌ テスト中にエラーが発生しました: {str(e)}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fixed_template_generation()
