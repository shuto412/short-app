from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict

class ProjectCreate(BaseModel):
    input_source: str = "url"  # "url" | "markdown"
    url: Optional[str] = None
    markdown_content: Optional[str] = None
    markdown_filename: Optional[str] = None
    scenario_type: str
    options: Optional[Dict] = {}

class Project(BaseModel):
    id: str
    url: Optional[str] = None
    title: Optional[str]
    input_source: str = "url"
    markdown_filename: Optional[str] = None
    scenario_type: str
    status: str
    created_at: datetime
    updated_at: datetime
