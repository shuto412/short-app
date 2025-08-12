"""
台本編集用データモデル
"""
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime

class VoiceSettings(BaseModel):
    """音声設定モデル"""
    emotion: str = Field(..., description="感情設定")
    speed: float = Field(1.0, ge=0.5, le=2.0, description="速度 (0.5-2.0)")
    pitch: float = Field(1.0, ge=0.5, le=2.0, description="ピッチ (0.5-2.0)")
    volume: float = Field(1.0, ge=0.0, le=2.0, description="音量 (0.0-2.0)")
    pause_length: float = Field(0.8, ge=0.0, le=2.0, description="ポーズ長 (0.0-2.0)")
    
    @validator('emotion')
    def validate_emotion(cls, v):
        valid_emotions = ['cheerful', 'confident', 'calm', 'excited', 'serious']
        if v not in valid_emotions:
            raise ValueError(f'感情は {valid_emotions} のいずれかである必要があります')
        return v

class EditableScene(BaseModel):
    """編集可能なシーンモデル"""
    scene_id: int = Field(..., description="シーンID")
    scene_type: str = Field(..., description="シーンタイプ")
    duration: float = Field(..., ge=0.1, description="シーン時間（秒）")
    text: str = Field(..., min_length=1, description="シーンテキスト")
    voice_settings: VoiceSettings = Field(..., description="音声設定")
    is_edited: bool = Field(False, description="編集済みフラグ")
    text_jp: Optional[str] = Field(None, description="シーンテキスト（ひらがな）")
    
    @validator('scene_type')
    def validate_scene_type(cls, v):
        valid_types = ['opening', 'main_content', 'explanation', 'demonstration', 'conclusion', 'cta']
        if v not in valid_types:
            raise ValueError(f'シーンタイプは {valid_types} のいずれかである必要があります')
        return v

class ScriptMetadata(BaseModel):
    """スクリプトメタデータ"""
    project_id: str = Field(..., description="プロジェクトID")
    title: str = Field(..., description="タイトル")
    scenario_type: str = Field(..., description="シナリオタイプ")
    total_duration: float = Field(..., ge=0, description="総時間")
    version: int = Field(1, ge=1, description="バージョン")
    edited: bool = Field(False, description="編集済みフラグ")
    last_edited: Optional[datetime] = Field(None, description="最終編集日時")

class EditableScript(BaseModel):
    """編集可能なスクリプトモデル"""
    metadata: ScriptMetadata = Field(..., description="メタデータ")
    scenes: List[EditableScene] = Field(..., description="シーン一覧")

class ScriptEditResponse(BaseModel):
    """スクリプト編集レスポンス"""
    success: bool = Field(..., description="成功フラグ")
    script: Optional[EditableScript] = Field(None, description="スクリプトデータ")
    message: Optional[str] = Field(None, description="メッセージ")

class SceneUpdateRequest(BaseModel):
    """シーン更新リクエスト"""
    text: Optional[str] = Field(None, description="テキスト")
    voice_settings: Optional[VoiceSettings] = Field(None, description="音声設定")
    duration: Optional[float] = Field(None, ge=0.1, description="時間")
    scene_type: Optional[str] = Field(None, description="シーンタイプ")
    text_jp: Optional[str] = Field(None, description="テキスト（ひらがな）")

class SceneUpdateResponse(BaseModel):
    """シーン更新レスポンス"""
    success: bool = Field(..., description="成功フラグ")
    scene: Optional[EditableScene] = Field(None, description="シーンデータ")
    message: Optional[str] = Field(None, description="メッセージ")

class SceneAddRequest(BaseModel):
    """シーン追加リクエスト"""
    scene_type: str = Field(..., description="シーンタイプ")
    text: str = Field(..., min_length=1, description="テキスト")
    voice_settings: Optional[VoiceSettings] = Field(None, description="音声設定")
    duration: float = Field(5.0, ge=0.1, description="時間")

class SceneReorderRequest(BaseModel):
    """シーン順序変更リクエスト"""
    scene_order: List[int] = Field(..., description="シーンIDの順序") 