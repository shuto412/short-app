from pydantic import BaseModel
from typing import List, Dict, Optional

class VoiceParameters(BaseModel):
    speed: float = 1.0
    volume: float = 1.0
    pitch: int = 0
    pauseLength: float = 0.8
    pauseLengthSentence: float = 1.0
    intonation: float = 1.0

class VoiceSegment(BaseModel):
    segment_id: int
    text: str
    start_time: float
    end_time: float
    parameters: VoiceParameters

class VoiceApiSettings(BaseModel):
    service: str = "nijivoice"
    voice_actor_id: str
    output_format: str = "wav"

class VoicePrompt(BaseModel):
    api_settings: VoiceApiSettings
    segments: List[VoiceSegment]

class VoiceActor(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    gender: Optional[str] = None
    age_range: Optional[str] = None 