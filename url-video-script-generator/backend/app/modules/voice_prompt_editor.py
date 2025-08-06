"""
音声設定編集モジュール
音声設定の取得・更新機能を提供
"""
import logging
import yaml
from typing import Dict, List, Optional
from app.modules.file_manager import FileManager

logger = logging.getLogger(__name__)

class VoicePromptEditor:
    """音声設定編集クラス"""
    
    def __init__(self):
        self.file_manager = FileManager()
    
    async def get_voice_prompt(self, project_id: str) -> Dict:
        """
        音声設定を取得
        
        Args:
            project_id: プロジェクトID
            
        Returns:
            Dict: 音声設定データ
        """
        try:
            if not self.file_manager.file_exists(project_id, "voice_prompt.yaml"):
                return {
                    "success": False,
                    "message": "音声設定ファイルが見つかりません"
                }
            
            voice_prompt_data = self.file_manager.load_yaml(project_id, "voice_prompt.yaml")
            
            return {
                "success": True,
                "voice_prompt": voice_prompt_data
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get voice prompt for {project_id}: {str(e)}")
            return {
                "success": False,
                "message": f"音声設定の取得に失敗しました: {str(e)}"
            }
    
    async def update_voice_prompt(self, project_id: str, settings_update: Dict) -> Dict:
        """
        音声設定を更新
        
        Args:
            project_id: プロジェクトID
            settings_update: 更新する音声設定データ
            
        Returns:
            Dict: 更新結果
        """
        try:
            # 現在の音声設定を取得
            current_settings = await self.get_voice_prompt(project_id)
            if not current_settings["success"]:
                return current_settings
            
            # 音声設定の構造を検証
            validation_result = self._validate_voice_prompt_structure(settings_update)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "message": validation_result["message"]
                }
            
            # 音声設定を更新
            updated_settings = self._merge_voice_prompt_data(current_settings["voice_prompt"], settings_update)
            
            # ファイルに保存
            self.file_manager.save_yaml(project_id, "voice_prompt.yaml", updated_settings)
            
            return {
                "success": True,
                "message": "音声設定を更新しました",
                "voice_prompt": updated_settings,
                "warnings": validation_result.get("warnings", [])
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to update voice prompt for {project_id}: {str(e)}")
            return {
                "success": False,
                "message": f"音声設定の更新に失敗しました: {str(e)}"
            }
    
    def _validate_voice_prompt_structure(self, voice_prompt_data: Dict) -> Dict:
        """
        音声設定の構造を検証
        
        Args:
            voice_prompt_data: 検証する音声設定データ
            
        Returns:
            Dict: 検証結果
        """
        warnings = []
        
        # 必須フィールドのチェック
        required_fields = ["voice_actor_id", "voice_speed", "prompts"]
        for field in required_fields:
            if field not in voice_prompt_data:
                return {
                    "valid": False,
                    "message": f"必須フィールド '{field}' が不足しています"
                }
        
        # voice_actor_idの検証
        voice_actor_id = voice_prompt_data.get("voice_actor_id")
        if not isinstance(voice_actor_id, str) or not voice_actor_id:
            return {
                "valid": False,
                "message": "voice_actor_idは有効な文字列である必要があります"
            }
        
        # voice_speedの検証
        voice_speed = voice_prompt_data.get("voice_speed")
        if not isinstance(voice_speed, (int, float)) or voice_speed <= 0:
            return {
                "valid": False,
                "message": "voice_speedは正の数値である必要があります"
            }
        
        # promptsフィールドの構造チェック
        if "prompts" in voice_prompt_data:
            prompts = voice_prompt_data["prompts"]
            if not isinstance(prompts, list):
                return {
                    "valid": False,
                    "message": "promptsフィールドは配列である必要があります"
                }
            
            # 各プロンプトの構造チェック
            for i, prompt in enumerate(prompts):
                if not isinstance(prompt, dict):
                    warnings.append(f"プロンプト {i+1} が不正な形式です")
                    continue
                
                if "text" not in prompt:
                    warnings.append(f"プロンプト {i+1} にテキストがありません")
                
                if "role" not in prompt:
                    warnings.append(f"プロンプト {i+1} にロールがありません")
        
        return {
            "valid": True,
            "warnings": warnings
        }
    
    def _merge_voice_prompt_data(self, current_settings: Dict, update_data: Dict) -> Dict:
        """
        音声設定データをマージ
        
        Args:
            current_settings: 現在の音声設定データ
            update_data: 更新データ
            
        Returns:
            Dict: マージされた音声設定データ
        """
        # 浅いコピーを作成
        merged_settings = current_settings.copy()
        
        # 更新データで上書き
        for key, value in update_data.items():
            merged_settings[key] = value
        
        return merged_settings 