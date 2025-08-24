#!/usr/bin/env python3
"""
FileManagerを使わずに、直接ファイルを読み込んでYAML解析をテストするスクリプト
"""

import yaml
import os

def test_direct_file_reading():
    """直接ファイル読み込みテスト"""
    print("=== 直接ファイル読み込みテスト ===")
    
    # テスト対象のファイルパス
    file_path = "DATA/a8bb22e3-a861-4c28-8cbb-53536c2ac7b7/summary.yaml"
    
    print(f"ファイルパス: {file_path}")
    print(f"ファイルの存在: {os.path.exists(file_path)}")
    
    if os.path.exists(file_path):
        try:
            # ファイルサイズの確認
            file_size = os.path.getsize(file_path)
            print(f"ファイルサイズ: {file_size} bytes")
            
            # ファイル権限の確認
            import stat
            file_stat = os.stat(file_path)
            print(f"ファイル権限: {oct(file_stat.st_mode)}")
            print(f"読み取り可能: {bool(file_stat.st_mode & stat.S_IRUSR)}")
            
            # ファイルの内容を読み込み
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"読み込まれた内容の長さ: {len(content)} 文字")
                print(f"最初の200文字: {repr(content[:200])}")
                print(f"最後の100文字: {repr(content[-100:])}")
                
                # 空行や特殊文字の確認
                print(f"空行の数: {content.count('')}")
                print(f"改行文字の数: {content.count('\\n')}")
                print(f"タブ文字の数: {content.count('\\t')}")
                
                # YAML解析のテスト
                try:
                    yaml_data = yaml.safe_load(content)
                    print(f"YAML解析成功: {type(yaml_data)}")
                    
                    if yaml_data and isinstance(yaml_data, dict):
                        print(f"トップレベルのキー: {list(yaml_data.keys())}")
                        
                        if 'product_info' in yaml_data:
                            product_info = yaml_data['product_info']
                            print(f"product_infoのキー: {list(product_info.keys())}")
                            
                            if 'product_name' in product_info:
                                product_name = product_info['product_name']
                                print(f"product_name: {product_name} (型: {type(product_name)})")
                                
                                if isinstance(product_name, list):
                                    print(f"product_nameの要素数: {len(product_name)}")
                                    for i, name in enumerate(product_name):
                                        print(f"  [{i}]: {name}")
                        else:
                            print("product_infoキーが見つかりません")
                    else:
                        print(f"YAMLデータが辞書ではありません: {yaml_data}")
                        
                except yaml.YAMLError as e:
                    print(f"YAML解析エラー: {e}")
                    print(f"エラー位置: {e.problem_mark}")
                    if hasattr(e, 'problem_mark') and e.problem_mark:
                        line_no = e.problem_mark.line + 1
                        column_no = e.problem_mark.column + 1
                        print(f"問題のある行: {line_no}, 列: {column_no}")
                        
                        # 問題のある行の内容を表示
                        lines = content.split('\n')
                        if line_no <= len(lines):
                            problem_line = lines[line_no - 1]
                            print(f"問題のある行の内容: {repr(problem_line)}")
                            
                except Exception as e:
                    print(f"予期しないエラー: {e}")
                    import traceback
                    traceback.print_exc()
                    
        except Exception as e:
            print(f"ファイル読み込みエラー: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("ファイルが存在しません")

if __name__ == "__main__":
    test_direct_file_reading()
