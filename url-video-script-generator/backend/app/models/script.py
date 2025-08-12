from pydantic import BaseModel
from typing import List, Optional, Dict

class VoiceSettings(BaseModel):
    emotion: str = "neutral"
    speed: float = 1.0
    pitch: float = 1.0

class Scene(BaseModel):
    scene_id: int
    scene_type: str
    duration: float
    text: str
    voice_settings: VoiceSettings
    text_jp: Optional[str] = None

class ScriptMetadata(BaseModel):
    project_id: str
    title: str
    scenario_type: str
    total_duration: float
    created_at: str

class Script(BaseModel):
    metadata: ScriptMetadata
    scenes: List[Scene]
