"""
台本編集API
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, List
from app.modules.script_editor import ScriptEditor
from app.models.script_edit import (
    EditableScript, SceneUpdateRequest, SceneAddRequest, SceneReorderRequest,
    ScriptEditResponse, SceneUpdateResponse
)
from app.utils.script_edit_errors import (
    ScriptEditError, handle_script_edit_error, raise_http_exception
)

router = APIRouter()
script_editor = ScriptEditor()

@router.get("/script/{project_id}", response_model=ScriptEditResponse)
async def get_script(project_id: str):
    """
    編集用台本を取得
    
    Args:
        project_id: プロジェクトID
        
    Returns:
        ScriptEditResponse: 台本データ
    """
    try:
        response = await script_editor.get_script(project_id)
        return response
    except ScriptEditError as e:
        raise_http_exception(e)
    except Exception as e:
        error_response = handle_script_edit_error(e)
        raise HTTPException(status_code=500, detail=error_response)

@router.put("/script/{project_id}", response_model=ScriptEditResponse)
async def update_script(project_id: str, script_update: EditableScript):
    """
    台本を更新
    
    Args:
        project_id: プロジェクトID
        script_update: 更新する台本データ
        
    Returns:
        ScriptEditResponse: 更新結果
    """
    try:
        response = await script_editor.update_script(project_id, script_update)
        return response
    except ScriptEditError as e:
        raise_http_exception(e)
    except Exception as e:
        error_response = handle_script_edit_error(e)
        raise HTTPException(status_code=500, detail=error_response)

@router.put("/script/{project_id}/scene/{scene_id}")
async def update_scene(project_id: str, scene_id: int, scene_update: SceneUpdateRequest):
    """
    個別シーンを更新
    
    Args:
        project_id: プロジェクトID
        scene_id: シーンID
        scene_update: シーン更新データ
        
    Returns:
        Dict: 更新結果
    """
    try:
        response = await script_editor.update_scene(project_id, scene_id, scene_update)
        return response
    except ScriptEditError as e:
        raise_http_exception(e)
    except Exception as e:
        error_response = handle_script_edit_error(e)
        raise HTTPException(status_code=500, detail=error_response)

@router.post("/script/{project_id}/scene")
async def add_scene(project_id: str, scene_data: SceneAddRequest):
    """
    新しいシーンを追加
    
    Args:
        project_id: プロジェクトID
        scene_data: シーン追加データ
        
    Returns:
        Dict: 追加結果
    """
    try:
        response = await script_editor.add_scene(project_id, scene_data)
        return response
    except ScriptEditError as e:
        raise_http_exception(e)
    except Exception as e:
        error_response = handle_script_edit_error(e)
        raise HTTPException(status_code=500, detail=error_response)

@router.delete("/script/{project_id}/scene/{scene_id}")
async def delete_scene(project_id: str, scene_id: int):
    """
    シーンを削除
    
    Args:
        project_id: プロジェクトID
        scene_id: シーンID
        
    Returns:
        Dict: 削除結果
    """
    try:
        response = await script_editor.delete_scene(project_id, scene_id)
        return response
    except ScriptEditError as e:
        raise_http_exception(e)
    except Exception as e:
        error_response = handle_script_edit_error(e)
        raise HTTPException(status_code=500, detail=error_response)

@router.put("/script/{project_id}/scenes/reorder")
async def reorder_scenes(project_id: str, reorder_request: SceneReorderRequest):
    """
    シーン順序を変更
    
    Args:
        project_id: プロジェクトID
        reorder_request: 順序変更リクエスト
        
    Returns:
        Dict: 順序変更結果
    """
    try:
        response = await script_editor.reorder_scenes(project_id, reorder_request.scene_order)
        return response
    except ScriptEditError as e:
        raise_http_exception(e)
    except Exception as e:
        error_response = handle_script_edit_error(e)
        raise HTTPException(status_code=500, detail=error_response) 