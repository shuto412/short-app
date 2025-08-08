"""
台本編集モジュール
台本の取得・更新・シーンCRUD・順序変更を提供
"""
import logging
from typing import Dict, List, Optional, Any

from app.modules.file_manager import FileManager
from app.utils.script_edit_errors import (
    ScriptNotFoundError,
    SceneNotFoundError,
    InvalidScriptStructureError,
    FileSaveError,
    SceneReorderError,
)
from app.models.script_edit import EditableScript, EditableScene, SceneUpdateRequest, SceneAddRequest

logger = logging.getLogger(__name__)


class ScriptEditor:
    """台本編集クラス"""

    def __init__(self):
        self.file_manager = FileManager()
        self.allowed_scene_types = {
            "opening",
            "main_content",
            "explanation",
            "demonstration",
            "conclusion",
            "cta",
        }
        self.scene_type_mapping = {
            "main": "main_content",
            "content": "main_content",
            "problem": "explanation",
            "solution": "demonstration",
            "closing": "conclusion",
            "end": "conclusion",
        }
        self.allowed_emotions = {"cheerful", "confident", "calm", "excited", "serious"}

    def _normalize_scene_type(self, raw_type: str) -> str:
        t = str(raw_type).lower().strip() if raw_type else "main_content"
        normalized = self.scene_type_mapping.get(t, t)
        return normalized if normalized in self.allowed_scene_types else "main_content"

    def _normalize_script_data(self, script_data: Dict[str, Any]) -> Dict[str, Any]:
        """旧フォーマットのシーンタイプ等を新仕様に正規化"""
        scenes = script_data.get("scenes", []) or []
        changed = False
        for scene in scenes:
            before = scene.get("scene_type")
            after = self._normalize_scene_type(before)
            if before != after:
                scene["scene_type"] = after
                changed = True
            # voice_settings 正規化
            vs = scene.get("voice_settings") or {}
            emotion = str(vs.get("emotion", "calm")).lower().strip()
            if emotion not in self.allowed_emotions:
                # neutral などは calm に寄せる
                emotion = "calm"
                changed = True
            # 数値域の補正とデフォルト補完
            def clamp(v, lo, hi, default):
                try:
                    fv = float(v)
                except Exception:
                    return default
                return max(lo, min(hi, fv))
            speed = clamp(vs.get("speed", 1.0), 0.5, 2.0, 1.0)
            pitch = clamp(vs.get("pitch", 1.0), 0.5, 2.0, 1.0)
            volume = clamp(vs.get("volume", 1.0), 0.0, 2.0, 1.0)
            pause_length = clamp(vs.get("pause_length", 0.8), 0.0, 2.0, 0.8)
            normalized_vs = {
                "emotion": emotion,
                "speed": speed,
                "pitch": pitch,
                "volume": volume,
                "pause_length": pause_length,
            }
            if vs != normalized_vs:
                scene["voice_settings"] = normalized_vs
                changed = True
            # is_edited のデフォルト補完
            if "is_edited" not in scene:
                scene["is_edited"] = False
                changed = True
        if changed:
            script_data["scenes"] = scenes
        return script_data

    async def get_script(self, project_id: str) -> Dict[str, Any]:
        """編集用台本を取得"""
        try:
            if not self.file_manager.file_exists(project_id, "script.yaml"):
                raise ScriptNotFoundError(project_id)

            script_data = await self.file_manager.read_file(project_id, "script.yaml")
            # 自動マイグレーション（scene_type 正規化など）
            script_data = self._normalize_script_data(script_data)
            # 検証前に正規化結果を保存（将来の読み込みを安定化）
            try:
                await self._save_with_backup(project_id, script_data)
            except Exception:
                # 保存失敗は致命ではないためログのみ
                logger.warning(f"⚠️ Failed to persist normalized script for {project_id}")
            # 受領データをEditableScriptとして検証（不整合時は例外）
            EditableScript.parse_obj(script_data)
            return {"success": True, "script": script_data}
        except ScriptNotFoundError:
            raise
        except Exception as e:
            logger.error(f"❌ Failed to get script for {project_id}: {str(e)}")
            raise InvalidScriptStructureError(str(e))

    async def _save_with_backup(self, project_id: str, script_data: Dict[str, Any]) -> None:
        try:
            # 既存があればバックアップ
            if self.file_manager.file_exists(project_id, "script.yaml"):
                current = await self.file_manager.read_file(project_id, "script.yaml")
                await self.file_manager.save_file(project_id, "script_backup.yaml", current)
            await self.file_manager.save_file(project_id, "script.yaml", script_data)
        except Exception as e:
            logger.error(f"❌ Failed to save script for {project_id}: {str(e)}")
            raise FileSaveError(project_id, str(e))

    async def update_script(self, project_id: str, script_update: Dict[str, Any]) -> Dict[str, Any]:
        """台本を更新（全体）"""
        try:
            current_result = await self.get_script(project_id)
            current_script = current_result["script"]

            # 入力をEditableScriptで検証
            try:
                # FastAPIで受けたモデルがPydanticモデルのまま来ることがあるためdict化
                if hasattr(script_update, 'dict'):
                    script_update = script_update.dict()
                EditableScript.parse_obj(script_update)
            except Exception as e:
                raise InvalidScriptStructureError(str(e))

            updated_script = self._merge_script_data(current_script, script_update)
            await self._save_with_backup(project_id, updated_script)
            return {"success": True, "message": "台本を更新しました", "script": updated_script}
        except (ScriptNotFoundError, InvalidScriptStructureError, FileSaveError):
            raise
        except Exception as e:
            logger.error(f"❌ Failed to update script for {project_id}: {str(e)}")
            raise InvalidScriptStructureError(str(e))

    async def update_scene(self, project_id: str, scene_id: int, scene_update: SceneUpdateRequest) -> Dict[str, Any]:
        """個別シーンを更新"""
        result = await self.get_script(project_id)
        script = result["script"]
        scenes: List[Dict[str, Any]] = script.get("scenes", [])

        # 対象シーン探索
        target_index = next((i for i, s in enumerate(scenes) if s.get("scene_id") == scene_id), None)
        if target_index is None:
            raise SceneNotFoundError(project_id, scene_id)

        updated_scene = {**scenes[target_index]}
        # 部分更新
        if scene_update.text is not None:
            updated_scene["text"] = scene_update.text
        if scene_update.voice_settings is not None:
            updated_scene["voice_settings"] = scene_update.voice_settings.dict()
        if scene_update.duration is not None:
            updated_scene["duration"] = scene_update.duration
        if scene_update.scene_type is not None:
            updated_scene["scene_type"] = scene_update.scene_type
        updated_scene["is_edited"] = True

        # 検証
        EditableScene.parse_obj(updated_scene)

        # 置き換え・保存
        scenes[target_index] = updated_scene
        script["scenes"] = scenes
        await self._save_with_backup(project_id, script)
        return {"success": True, "scene": updated_scene}

    async def add_scene(self, project_id: str, scene_data: SceneAddRequest) -> Dict[str, Any]:
        """新しいシーンを末尾に追加"""
        result = await self.get_script(project_id)
        script = result["script"]
        scenes: List[Dict[str, Any]] = script.get("scenes", [])

        new_id = (max([s.get("scene_id", 0) for s in scenes]) + 1) if scenes else 1
        new_scene_dict: Dict[str, Any] = {
            "scene_id": new_id,
            "scene_type": scene_data.scene_type,
            "duration": scene_data.duration,
            "text": scene_data.text,
            "voice_settings": (scene_data.voice_settings.dict() if scene_data.voice_settings else {
                "emotion": "cheerful",
                "speed": 1.0,
                "pitch": 1.0,
                "volume": 1.0,
                "pause_length": 0.8,
            }),
            "is_edited": True,
        }

        # 検証
        EditableScene.parse_obj(new_scene_dict)

        scenes.append(new_scene_dict)
        script["scenes"] = scenes
        await self._save_with_backup(project_id, script)
        return {"success": True, "scene": new_scene_dict}

    async def delete_scene(self, project_id: str, scene_id: int) -> Dict[str, Any]:
        """シーンを削除"""
        result = await self.get_script(project_id)
        script = result["script"]
        scenes: List[Dict[str, Any]] = script.get("scenes", [])

        if not any(s.get("scene_id") == scene_id for s in scenes):
            raise SceneNotFoundError(project_id, scene_id)

        scenes = [s for s in scenes if s.get("scene_id") != scene_id]
        script["scenes"] = scenes
        await self._save_with_backup(project_id, script)
        return {"success": True, "message": "シーンを削除しました"}

    async def reorder_scenes(self, project_id: str, scene_order: List[int]) -> Dict[str, Any]:
        """シーン順序を変更（scene_idは維持）"""
        result = await self.get_script(project_id)
        script = result["script"]
        scenes: List[Dict[str, Any]] = script.get("scenes", [])

        current_ids = [s.get("scene_id") for s in scenes]
        if sorted(current_ids) != sorted(scene_order):
            raise SceneReorderError(project_id, "scene_order が既存ID集合と一致しません")

        scene_map = {s["scene_id"]: s for s in scenes}
        reordered = [scene_map[i] for i in scene_order]
        script["scenes"] = reordered
        await self._save_with_backup(project_id, script)
        return {"success": True, "message": "シーン順序を更新しました", "script": script}

    def _validate_script_structure(self, script_data: Dict[str, Any]) -> Dict[str, Any]:
        """EditableScript 準拠で検証"""
        try:
            EditableScript.parse_obj(script_data)
            return {"valid": True, "warnings": []}
        except Exception as e:
            return {"valid": False, "message": str(e)}

    def _merge_script_data(self, current_script: Dict[str, Any], update_data: Dict[str, Any]) -> Dict[str, Any]:
        """浅いマージ（メタデータ/シーン配列は上書き）"""
        merged = {**current_script, **update_data}
        return merged