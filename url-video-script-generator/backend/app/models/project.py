from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict
from enum import Enum


class ProjectStage(str, Enum):
    URL_INPUT = "URL_INPUT"
    SCRAPING = "SCRAPING"
    SUMMARIZING = "SUMMARIZING"
    SCRIPT_GENERATING = "SCRIPT_GENERATING"
    SCRIPT_EDITING = "SCRIPT_EDITING"
    VOICE_SETTINGS_EDITING = "VOICE_SETTINGS_EDITING"
    VOICE_GENERATING = "VOICE_GENERATING"
    COMPLETED = "COMPLETED"

class ProjectCreate(BaseModel):
    url: str
    scenario_type: str
    options: Optional[Dict] = {}

class Project(BaseModel):
    id: str
    url: str
    title: Optional[str]
    scenario_type: str
    status: str
    created_at: datetime
    updated_at: datetime
    # 追加フィールド（段階実行管理用）
    current_stage: ProjectStage = ProjectStage.URL_INPUT
    can_edit_script: bool = False
    can_edit_voice: bool = False
