from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict

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