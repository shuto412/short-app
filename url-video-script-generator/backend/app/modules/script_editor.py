"""
台本編集モジュール
台本の取得・更新機能を提供
"""
import logging
import yaml
from typing import Dict, List, Optional
from app.modules.file_manager import FileManager

logger = logging.getLogger(__name__)

class ScriptEditor:
    """台本編集クラス"""
    
    def __init__(self):
        self.file_manager = FileManager()
    
    async def get_script(self, project_id: str) -> Dict:
        """
        台本を取得
        
        Args:
            project_id: プロジェクトID
            
        Returns:
            Dict: 台本データ
        """
        try:
            if not self.file_manager.file_exists(project_id, "script.yaml"):
                return {
                    "success": False,
                    "message": "台本ファイルが見つかりません"
                }
            
            script_data = self.file_manager.load_yaml(project_id, "script.yaml")
            
            return {
                "success": True,
                "script": script_data
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get script for {project_id}: {str(e)}")
            return {
                "success": False,
                "message": f"台本の取得に失敗しました: {str(e)}"
            }
    
    async def update_script(self, project_id: str, script_update: Dict) -> Dict:
        """
        台本を更新
        
        Args:
            project_id: プロジェクトID
            script_update: 更新する台本データ
            
        Returns:
            Dict: 更新結果
        """
        try:
            # 現在の台本を取得
            current_script = await self.get_script(project_id)
            if not current_script["success"]:
                return current_script
            
            # 台本の構造を検証
            validation_result = self._validate_script_structure(script_update)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "message": validation_result["message"]
                }
            
            # 台本を更新
            updated_script = self._merge_script_data(current_script["script"], script_update)
            
            # ファイルに保存
            self.file_manager.save_yaml(project_id, "script.yaml", updated_script)
            
            return {
                "success": True,
                "message": "台本を更新しました",
                "script": updated_script,
                "warnings": validation_result.get("warnings", [])
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to update script for {project_id}: {str(e)}")
            return {
                "success": False,
                "message": f"台本の更新に失敗しました: {str(e)}"
            }
    
    def _validate_script_structure(self, script_data: Dict) -> Dict:
        """
        台本の構造を検証
        
        Args:
            script_data: 検証する台本データ
            
        Returns:
            Dict: 検証結果
        """
        warnings = []
        
        # 必須フィールドのチェック
        required_fields = ["title", "scenario_type", "content"]
        for field in required_fields:
            if field not in script_data:
                return {
                    "valid": False,
                    "message": f"必須フィールド '{field}' が不足しています"
                }
        
        # contentフィールドの構造チェック
        if "content" in script_data:
            content = script_data["content"]
            if not isinstance(content, list):
                return {
                    "valid": False,
                    "message": "contentフィールドは配列である必要があります"
                }
            
            # 各セクションの構造チェック
            for i, section in enumerate(content):
                if not isinstance(section, dict):
                    warnings.append(f"セクション {i+1} が不正な形式です")
                    continue
                
                if "title" not in section:
                    warnings.append(f"セクション {i+1} にタイトルがありません")
                
                if "text" not in section:
                    warnings.append(f"セクション {i+1} にテキストがありません")
        
        return {
            "valid": True,
            "warnings": warnings
        }
    
    def _merge_script_data(self, current_script: Dict, update_data: Dict) -> Dict:
        """
        台本データをマージ
        
        Args:
            current_script: 現在の台本データ
            update_data: 更新データ
            
        Returns:
            Dict: マージされた台本データ
        """
        # 浅いコピーを作成
        merged_script = current_script.copy()
        
        # 更新データで上書き
        for key, value in update_data.items():
            merged_script[key] = value
        
        return merged_script 