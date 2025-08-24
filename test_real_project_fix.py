#!/usr/bin/env python3
"""
実際のプロジェクトデータを使用した修正後のScriptGeneratorのテスト
"""

import sys
import os
import yaml

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.join(os.path.dirname(__file__), 'url-video-script-generator', 'backend'))

from app.modules.script_generator import ScriptGenerator

def test_real_project_data():
    """実際のプロジェクトデータでテスト"""
    
    try:
        # 実際のsummary.yamlファイルのパス
        summary_file_path = 'DATA/1890a32e-d5a6-4944-a8ed-760f67b39cae/summary.yaml'
        
        # summary.yamlファイルを読み込み
        with open(summary_file_path, 'r', encoding='utf-8') as f:
            summary_content = f.read()
        
        print("=== 実際のプロジェクトデータのテスト ===")
        print(f"使用するファイル: {summary_file_path}")
        
        # ScriptGeneratorのインスタンスを作成
        generator = ScriptGenerator(claude_client=None)
        
        # summary.yamlを解析
        summary_data = generator._parse_summary_yaml(summary_content)
        print('\n=== 実際のsummary.yamlから抽出されたデータ ===')
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
        
        # 特定の変数が正しく置換されているかチェック
        print('\n=== 置換結果の検証 ===')
        
        # product_nameが配列形式から正しく抽出されているかチェック
        expected_product_name = "X2 v3 Gaming Mouse"
        all_sections_contain_product_name = True
        
        for i, section in enumerate(replaced_template['structure']):
            contains_product_name = expected_product_name in section['description']
            print(f'セクション{i+1} ({section["name"]}) にproduct_nameが含まれている: {contains_product_name}')
            if not contains_product_name:
                all_sections_contain_product_name = False
        
        print(f'\nすべてのセクションでproduct_nameが正しく置換されている: {all_sections_contain_product_name}')
        
        # 元のスクリプトと比較
        script_file_path = 'DATA/1890a32e-d5a6-4944-a8ed-760f67b39cae/script.yaml'
        if os.path.exists(script_file_path):
            with open(script_file_path, 'r', encoding='utf-8') as f:
                current_script = yaml.safe_load(f)
            
            print('\n=== 現在のスクリプトとの比較 ===')
            print('現在のスクリプトでは「製品」という汎用的な言葉が使用されている')
            print('修正後は「X2 v3 Gaming Mouse」という具体的な製品名が使用されるはず')
        
        return all_sections_contain_product_name
        
    except Exception as e:
        print(f'テスト実行中にエラーが発生: {str(e)}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_real_project_data()
    
    if success:
        print("\n✅ 実際のプロジェクトデータでのテスト: 成功")
        print("配列形式のproduct_name問題が解決されました！")
    else:
        print("\n❌ 実際のプロジェクトデータでのテスト: 失敗")
        print("問題が残っている可能性があります")
