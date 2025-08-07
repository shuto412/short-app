"""
台本編集機能用エラーハンドリング
"""
from typing import Dict, Any
from fastapi import HTTPException

class ScriptEditError(Exception):
    """台本編集エラーの基底クラス"""
    def __init__(self, error_code: str, message: str, details: Dict[str, Any] = None):
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        super().__init__(message)

class ScriptNotFoundError(ScriptEditError):
    """台本が見つからないエラー"""
    def __init__(self, project_id: str):
        super().__init__(
            "E001",
            f"台本が見つかりません: {project_id}",
            {"project_id": project_id}
        )

class SceneNotFoundError(ScriptEditError):
    """シーンが見つからないエラー"""
    def __init__(self, project_id: str, scene_id: int):
        super().__init__(
            "E002",
            f"シーンが見つかりません: {project_id}/scene/{scene_id}",
            {"project_id": project_id, "scene_id": scene_id}
        )

class InvalidScriptStructureError(ScriptEditError):
    """台本構造が無効なエラー"""
    def __init__(self, details: str):
        super().__init__(
            "E003",
            f"台本構造が無効です: {details}",
            {"details": details}
        )

class FileSaveError(ScriptEditError):
    """ファイル保存エラー"""
    def __init__(self, project_id: str, error: str):
        super().__init__(
            "E004",
            f"ファイル保存に失敗しました: {project_id}",
            {"project_id": project_id, "error": error}
        )

class SceneReorderError(ScriptEditError):
    """シーン順序変更エラー"""
    def __init__(self, project_id: str, details: str):
        super().__init__(
            "E005",
            f"シーン順序変更に失敗しました: {details}",
            {"project_id": project_id, "details": details}
        )

# エラーコード定義
SCRIPT_EDIT_ERRORS = {
    "E001": "Script not found",
    "E002": "Scene not found", 
    "E003": "Invalid script structure",
    "E004": "File save failed",
    "E005": "Scene reorder failed"
}

def create_error_response(error: ScriptEditError) -> Dict[str, Any]:
    """
    エラーレスポンスを作成
    
    Args:
        error: ScriptEditError
        
    Returns:
        Dict: エラーレスポンス
    """
    return {
        "success": False,
        "error": error.error_code,
        "message": error.message,
        "details": error.details
    }

def handle_script_edit_error(error: Exception) -> Dict[str, Any]:
    """
    台本編集エラーをハンドリング
    
    Args:
        error: 発生したエラー
        
    Returns:
        Dict: エラーレスポンス
    """
    if isinstance(error, ScriptEditError):
        return create_error_response(error)
    
    # 予期しないエラーの場合
    return {
        "success": False,
        "error": "E999",
        "message": f"予期しないエラーが発生しました: {str(error)}",
        "details": {"error_type": type(error).__name__}
    }

def raise_http_exception(error: ScriptEditError):
    """
    HTTPExceptionを発生させる
    
    Args:
        error: ScriptEditError
    """
    raise HTTPException(
        status_code=400,
        detail=create_error_response(error)
    ) 