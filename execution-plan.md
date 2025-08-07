# URL動画台本生成システム - 実行計画書

## フェーズ1: 開発環境セットアップ（Day 1）

### タスク1.1: プロジェクト初期化
```bash
# ディレクトリ作成
mkdir url-video-script-generator
cd url-video-script-generator
mkdir frontend backend DATA

# Gitリポジトリ初期化
git init
echo "# URL Video Script Generator" > README.md

# .gitignore作成
cat > .gitignore << EOF
# Python
__pycache__/
*.py[cod]
.env
venv/

# Node
node_modules/
build/
dist/

# Data
DATA/*
!DATA/.gitkeep

# IDE
.vscode/
.idea/
EOF

touch DATA/.gitkeep
```

### タスク1.2: バックエンド環境構築
```bash
cd backend

# Python仮想環境作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# requirements.txt作成
cat > requirements.txt << EOF
fastapi==0.104.1
uvicorn==0.24.0
python-dotenv==1.0.0
requests==2.31.0
beautifulsoup4==4.12.2
selenium==4.15.2
anthropic==0.7.0
pyyaml==6.0.1
aiofiles==23.2.1
pydantic==2.5.0
python-multipart==0.0.6
EOF

pip install -r requirements.txt

# ディレクトリ構造作成
mkdir -p app/{models,modules,api,templates}
touch app/__init__.py
touch app/{main.py,config.py}
touch app/models/__init__.py
touch app/modules/__init__.py
touch app/api/__init__.py
```

### タスク1.3: フロントエンド環境構築
```bash
cd ../frontend

# React プロジェクト作成
npx create-react-app . --template typescript

# 追加パッケージインストール
npm install axios react-query @mui/material @emotion/react @emotion/styled

# ディレクトリ構造作成
mkdir -p src/{components,services,types}
touch src/services/api.ts
touch src/types/index.ts
```

## フェーズ2: バックエンド基礎実装（Day 2-3）

### タスク2.1: 設定ファイルと基本構造
```python
# backend/app/config.py を作成
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
    NIJIVOICE_API_KEY = os.getenv("NIJIVOICE_API_KEY")
    DATA_DIR = os.getenv("DATA_DIR", "../../DATA")
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    BACKEND_PORT = int(os.getenv("BACKEND_PORT", 8080))
    
settings = Settings()
"""

# backend/.env ファイルを作成
"""
CLAUDE_API_KEY=your_key_here
NIJIVOICE_API_KEY=your_key_here
DATA_DIR=../../DATA
BACKEND_PORT=8080
"""
```

### タスク2.2: データモデル実装
```python
# backend/app/models/project.py を作成
"""
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
"""

# 同様にscript.py, voice.pyも作成
```

### タスク2.3: FastAPI基本実装
```python
# backend/app/main.py を作成
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

app = FastAPI(title="URL Video Script Generator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "URL Video Script Generator API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.BACKEND_PORT)
"""
```

## フェーズ3: スクレイピングモジュール実装（Day 4-5）

### タスク3.1: スクレイピング基本実装
```python
# backend/app/modules/scraper.py を作成
"""
import requests
from bs4 import BeautifulSoup
from typing import Optional
import logging

class Scraper:
    def __init__(self):
        self.session = requests.Session()
        self.logger = logging.getLogger(__name__)
    
    async def scrape(self, url: str) -> str:
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # スクリプトとスタイルタグを削除
            for script in soup(["script", "style"]):
                script.decompose()
            
            # テキスト抽出
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
        except Exception as e:
            self.logger.error(f"Scraping failed: {str(e)}")
            raise
"""
```

### タスク3.2: 動的サイト対応
```python
# Selenium対応を追加
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def setup_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    return webdriver.Chrome(options=options)

async def scrape_dynamic(self, url: str) -> str:
    driver = self.setup_driver()
    try:
        driver.get(url)
        # ページ読み込み待機
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        return driver.find_element(By.TAG_NAME, "body").text
    finally:
        driver.quit()
"""
```

## フェーズ4: Claude API連携実装（Day 6-7）

### タスク4.1: Claude API クライアント実装
```python
# backend/app/modules/summarizer.py を作成
"""
import anthropic
from typing import Dict
from app.config import settings

class ClaudeClient:
    def __init__(self):
        self.client = anthropic.Client(api_key=settings.CLAUDE_API_KEY)
    
    async def summarize(self, content: str, max_length: int = 500) -> str:
        prompt = f'''
        以下のコンテンツを{max_length}文字以内で要約してください。
        重要なポイントを箇条書きで抽出し、動画制作に役立つ情報を中心にまとめてください。
        
        コンテンツ:
        {content}
        '''
        
        response = self.client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
"""
```

### タスク4.2: 台本生成機能実装
```python
# backend/app/modules/script_generator.py を作成
"""
from typing import Dict
import yaml
from datetime import datetime

class ScriptGenerator:
    def __init__(self, claude_client):
        self.claude = claude_client
    
    async def generate(self, summary: str, scenario_type: str, target_duration: int = 60) -> Dict:
        # テンプレート読み込み
        template = self.load_template(scenario_type)
        
        prompt = f'''
        以下の要約から{target_duration}秒の動画台本を生成してください。
        シナリオタイプ: {scenario_type}
        
        要約:
        {summary}
        
        以下の形式でYAML形式で出力してください:
        - scene_id: シーン番号
        - scene_type: シーンタイプ
        - duration: 秒数
        - text: セリフ
        - voice_settings: 音声設定
        '''
        
        response = await self.claude.client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # YAML解析して返す
        script_data = yaml.safe_load(response.content[0].text)
        
        return {
            "metadata": {
                "project_id": "",  # 後で設定
                "title": "生成された動画",
                "scenario_type": scenario_type,
                "total_duration": target_duration,
                "created_at": datetime.now().isoformat()
            },
            "scenes": script_data
        }
"""
```

## フェーズ5: 音声・字幕生成実装（Day 8-9）

### タスク5.1: 音声生成API連携
```python
# backend/app/modules/voice_generator.py を作成
"""
import aiohttp
from typing import Dict, List, Optional
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class VoiceGenerator:
    def __init__(self):
        self.api_key = settings.NIJIVOICE_API_KEY
        self.base_url = "https://api.nijivoice.com/api/platform/v1"
        
    async def get_voice_actors(self) -> List[Dict]:
        \"\"\"利用可能なボイスアクター一覧を取得\"\"\"
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with session.get(
                f"{self.base_url}/voice-actors",
                headers=headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to get voice actors: {response.status}")
    
    async def generate(self, voice_actor_id: str, text: str, options: Optional[Dict] = None) -> bytes:
        \"\"\"音声を生成\"\"\"
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # デフォルトパラメータ
            data = {
                "text": text,
                "format": "wav",
                "speed": 1.0,
                "volume": 1.0,
                "pitch": 0,
                "pauseLength": 0.8,
                "pauseLengthSentence": 1.0,
                "intonation": 1.0
            }
            
            # オプションパラメータがあれば上書き
            if options:
                data.update(options)
            
            async with session.post(
                f"{self.base_url}/voice-actors/{voice_actor_id}/generate-voice",
                headers=headers,
                json=data
            ) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    error_text = await response.text()
                    logger.error(f"Voice generation failed: {response.status} - {error_text}")
                    raise Exception(f"Voice generation failed: {response.status}")
    
    async def generate_from_script(self, voice_prompt: Dict) -> bytes:
        \"\"\"スクリプトから音声を生成（複数セグメントを結合）\"\"\"
        voice_actor_id = voice_prompt["api_settings"]["voice_actor_id"]
        audio_segments = []
        
        for segment in voice_prompt["segments"]:
            try:
                audio_data = await self.generate(
                    voice_actor_id=voice_actor_id,
                    text=segment["text"],
                    options=segment.get("parameters", {})
                )
                audio_segments.append(audio_data)
            except Exception as e:
                logger.error(f"Failed to generate segment {segment['segment_id']}: {str(e)}")
                raise
        
        # 音声セグメントを結合（簡易版 - 実際はwaveファイルの適切な結合が必要）
        return b''.join(audio_segments)
    
    def create_voice_prompt(self, script: Dict, voice_actor_id: str) -> Dict:
        \"\"\"スクリプトから音声生成用プロンプトを作成\"\"\"
        return {
            "api_settings": {
                "service": "nijivoice",
                "voice_actor_id": voice_actor_id,
                "output_format": "wav"
            },
            "segments": [
                {
                    "segment_id": scene["scene_id"],
                    "text": scene["text"],
                    "start_time": sum(s["duration"] for s in script["scenes"][:i]),
                    "end_time": sum(s["duration"] for s in script["scenes"][:i+1]),
                    "parameters": {
                        "speed": scene.get("voice_settings", {}).get("speed", 1.0),
                        "pitch": scene.get("voice_settings", {}).get("pitch", 0),
                        "volume": 1.0,
                        "pauseLength": 0.8,
                        "pauseLengthSentence": 1.0,
                        "intonation": 1.0
                    }
                }
                for i, scene in enumerate(script["scenes"])
            ]
        }
"""
```

### タスク5.2: 字幕生成実装
```python
# backend/app/modules/subtitle_generator.py を作成
"""
from typing import List, Dict

class SubtitleGenerator:
    def generate_srt(self, script: Dict) -> str:
        srt_content = []
        current_time = 0.0
        
        for i, scene in enumerate(script["scenes"], 1):
            start_time = current_time
            end_time = current_time + scene["duration"]
            
            # SRT時間形式に変換
            start_str = self._format_time(start_time)
            end_str = self._format_time(end_time)
            
            srt_content.append(f"{i}")
            srt_content.append(f"{start_str} --> {end_str}")
            srt_content.append(scene["text"])
            srt_content.append("")  # 空行
            
            current_time = end_time
        
        return "\n".join(srt_content)
    
    def _format_time(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        millisecs = int((secs % 1) * 1000)
        secs = int(secs)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
"""
```

## フェーズ6: ファイル管理システム実装（Day 10）

### タスク6.1: ファイル管理モジュール
```python
# backend/app/modules/file_manager.py を作成
"""
import os
import aiofiles
from typing import Any
import yaml
import json
from app.config import settings

class FileManager:
    def __init__(self):
        self.base_dir = settings.DATA_DIR
    
    async def create_project_dir(self, project_id: str) -> str:
        project_path = os.path.join(self.base_dir, project_id)
        os.makedirs(project_path, exist_ok=True)
        return project_path
    
    async def save_file(self, project_id: str, filename: str, content: Any):
        project_path = await self.create_project_dir(project_id)
        file_path = os.path.join(project_path, filename)
        
        if filename.endswith('.yaml'):
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(yaml.dump(content, allow_unicode=True))
        elif filename.endswith('.json'):
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(content, ensure_ascii=False, indent=2))
        elif isinstance(content, bytes):
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
        else:
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(str(content))
    
    async def read_file(self, project_id: str, filename: str) -> Any:
        file_path = os.path.join(self.base_dir, project_id, filename)
        
        if filename.endswith('.yaml'):
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                return yaml.safe_load(content)
        elif filename.endswith('.json'):
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                return json.loads(content)
        elif filename.endswith(('.wav', '.mp3')):
            async with aiofiles.open(file_path, 'rb') as f:
                return await f.read()
        else:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                return await f.read()
    
    def list_project_files(self, project_id: str) -> List[str]:
        project_path = os.path.join(self.base_dir, project_id)
        if os.path.exists(project_path):
            return os.listdir(project_path)
        return []
"""
```

## フェーズ7: APIエンドポイント実装（Day 11-12）

### タスク7.1: プロジェクトAPI実装
```python
# backend/app/api/project.py を作成
"""
from fastapi import APIRouter, HTTPException
from typing import List
import uuid
from datetime import datetime
from app.models.project import Project, ProjectCreate
from app.modules.file_manager import FileManager

router = APIRouter(prefix="/api/projects", tags=["projects"])
file_manager = FileManager()

# 一時的なメモリストレージ（実際はDBを使用）
projects_db = {}

@router.post("/")
async def create_project(project: ProjectCreate):
    project_id = str(uuid.uuid4())
    
    new_project = Project(
        id=project_id,
        url=project.url,
        title=f"Project {project_id[:8]}",
        scenario_type=project.scenario_type,
        status="created",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    projects_db[project_id] = new_project
    await file_manager.create_project_dir(project_id)
    
    return {
        "project_id": project_id,
        "status": "created",
        "message": "Project created successfully"
    }

@router.get("/{project_id}")
async def get_project(project_id: str):
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return projects_db[project_id]

@router.get("/{project_id}/status")
async def get_project_status(project_id: str):
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {
        "project_id": project_id,
        "status": projects_db[project_id].status,
        "files": file_manager.list_project_files(project_id)
    }
"""
```

### タスク7.2: 生成処理API実装
```python
# backend/app/api/generation.py を作成
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.modules.scraper import Scraper
from app.modules.summarizer import ClaudeClient
from app.modules.script_generator import ScriptGenerator
from app.modules.voice_generator import VoiceGenerator
from app.modules.subtitle_generator import SubtitleGenerator
from app.modules.file_manager import FileManager

router = APIRouter(prefix="/api/generate", tags=["generation"])

# モジュールの初期化
scraper = Scraper()
claude_client = ClaudeClient()
script_generator = ScriptGenerator(claude_client)
voice_generator = VoiceGenerator()
subtitle_generator = SubtitleGenerator()
file_manager = FileManager()

async def process_project_task(project_id: str, url: str, scenario_type: str, voice_actor_id: str = None):
    try:
        # プロジェクトステータス更新
        if project_id in projects_db:
            projects_db[project_id].status = "processing"
        
        # 1. スクレイピング
        scraped_content = await scraper.scrape(url)
        await file_manager.save_file(project_id, "scraped_content.txt", scraped_content)
        
        # 2. 要約生成
        summary = await claude_client.summarize(scraped_content)
        await file_manager.save_file(project_id, "summary.txt", summary)
        
        # 3. 台本生成
        script = await script_generator.generate(summary, scenario_type)
        script["metadata"]["project_id"] = project_id
        await file_manager.save_file(project_id, "script.yaml", script)
        
        # 4. ボイスアクター選択（指定がない場合はデフォルト）
        if not voice_actor_id:
            voice_actors = await voice_generator.get_voice_actors()
            if voice_actors:
                voice_actor_id = voice_actors[0]["id"]  # 最初のアクターを使用
            else:
                raise Exception("No voice actors available")
        
        # 5. 音声生成用プロンプト作成
        voice_prompt = voice_generator.create_voice_prompt(script, voice_actor_id)
        await file_manager.save_file(project_id, "voice_prompt.yaml", voice_prompt)
        
        # 6. 音声生成
        audio_data = await voice_generator.generate_from_script(voice_prompt)
        await file_manager.save_file(project_id, "audio.wav", audio_data)
        
        # 7. 字幕生成
        subtitle = subtitle_generator.generate_srt(script)
        await file_manager.save_file(project_id, "subtitle.srt", subtitle)
        
        # ステータス更新
        if project_id in projects_db:
            projects_db[project_id].status = "completed"
            
    except Exception as e:
        if project_id in projects_db:
            projects_db[project_id].status = "failed"
        raise

@router.post("/process")
async def process_full(
    project_id: str,
    background_tasks: BackgroundTasks,
    voice_actor_id: str = None
):
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = projects_db[project_id]
    
    # バックグラウンドタスクとして実行
    background_tasks.add_task(
        process_project_task,
        project_id,
        project.url,
        project.scenario_type,
        voice_actor_id
    )
    
    return {
        "message": "Processing started",
        "project_id": project_id
    }

@router.get("/voice-actors")
async def get_voice_actors():
    \"\"\"利用可能なボイスアクター一覧を取得\"\"\"
    try:
        voice_actors = await voice_generator.get_voice_actors()
        return {"voice_actors": voice_actors}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scenarios")
async def get_scenarios():
    return {
        "scenarios": [
            {
                "id": "product_introduction",
                "name": "製品紹介",
                "description": "製品の特徴や利点を紹介"
            },
            {
                "id": "tutorial",
                "name": "使い方説明",
                "description": "ステップバイステップの説明"
            },
            {
                "id": "feature_explanation",
                "name": "機能説明",
                "description": "特定機能の詳細説明"
            }
        ]
    }
"""
```

### タスク7.3: ファイルダウンロードAPI実装
```python
# backend/app/api/generation.py に追加
"""
from fastapi.responses import FileResponse
import os

@router.get("/download/{project_id}/{file_type}")
async def download_file(project_id: str, file_type: str):
    file_mapping = {
        "script": "script.yaml",
        "audio": "audio.wav",
        "subtitle": "subtitle.srt",
        "summary": "summary.txt"
    }
    
    if file_type not in file_mapping:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    filename = file_mapping[file_type]
    file_path = os.path.join(settings.DATA_DIR, project_id, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        media_type="application/octet-stream",
        filename=filename
    )
"""
```

## フェーズ8: フロントエンド基本実装（Day 13-14）

### タスク8.1: API通信サービス実装
```typescript
// frontend/src/services/api.ts を作成
/*
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8080/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface ProjectCreate {
  url: string;
  scenario_type: string;
  options?: Record<string, any>;
}

export interface Project {
  id: string;
  url: string;
  title: string;
  scenario_type: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Scenario {
  id: string;
  name: string;
  description: string;
}

export const projectAPI = {
  create: async (data: ProjectCreate) => {
    const response = await api.post<{ project_id: string }>('/projects', data);
    return response.data;
  },
  
  get: async (projectId: string) => {
    const response = await api.get<Project>(`/projects/${projectId}`);
    return response.data;
  },
  
  getStatus: async (projectId: string) => {
    const response = await api.get(`/projects/${projectId}/status`);
    return response.data;
  },
};

export const generationAPI = {
  process: async (projectId: string) => {
    const response = await api.post('/generate/process', null, {
      params: { project_id: projectId }
    });
    return response.data;
  },
  
  getScenarios: async () => {
    const response = await api.get<{ scenarios: Scenario[] }>('/generate/scenarios');
    return response.data.scenarios;
  },
  
  download: (projectId: string, fileType: string) => {
    return `${API_BASE_URL}/generate/download/${projectId}/${fileType}`;
  },
};
*/
```

### タスク8.2: TypeScript型定義
```typescript
// frontend/src/types/index.ts を作成
/*
export interface ProjectCreate {
  url: string;
  scenario_type: string;
  options?: {
    target_duration?: number;
    voice_type?: string;
  };
}

export interface Project {
  id: string;
  url: string;
  title: string;
  scenario_type: string;
  status: 'created' | 'processing' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
}

export interface Scenario {
  id: string;
  name: string;
  description: string;
}

export interface GeneratedFile {
  name: string;
  type: 'script' | 'audio' | 'subtitle' | 'summary';
  downloadUrl: string;
}

export interface ProcessingStatus {
  project_id: string;
  status: string;
  files: string[];
}
*/
```

## フェーズ9: フロントエンド画面実装（Day 15-16）

### タスク9.1: URL入力コンポーネント
```typescript
// frontend/src/components/UrlInput.tsx を作成
/*
import React, { useState } from 'react';
import { TextField, Button, Box, Typography } from '@mui/material';

interface UrlInputProps {
  onSubmit: (url: string) => void;
}

export const UrlInput: React.FC<UrlInputProps> = ({ onSubmit }) => {
  const [url, setUrl] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // URL検証
    try {
      new URL(url);
      setError('');
      onSubmit(url);
    } catch {
      setError('有効なURLを入力してください');
    }
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ mt: 4 }}>
      <Typography variant="h4" gutterBottom>
        URLから動画台本を生成
      </Typography>
      
      <TextField
        fullWidth
        label="URL"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        error={!!error}
        helperText={error}
        placeholder="https://example.com"
        sx={{ mb: 2 }}
      />
      
      <Button
        type="submit"
        variant="contained"
        fullWidth
        disabled={!url}
      >
        次へ
      </Button>
    </Box>
  );
};
*/
```

### タスク9.2: シナリオ選択コンポーネント
```typescript
// frontend/src/components/ScenarioSelector.tsx を作成
/*
import React from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  CardActionArea,
  Grid,
} from '@mui/material';
import { Scenario } from '../types';

interface ScenarioSelectorProps {
  scenarios: Scenario[];
  onSelect: (scenarioType: string) => void;
}

export const ScenarioSelector: React.FC<ScenarioSelectorProps> = ({
  scenarios,
  onSelect,
}) => {
  return (
    <Box sx={{ mt: 4 }}>
      <Typography variant="h4" gutterBottom>
        シナリオを選択
      </Typography>
      
      <Grid container spacing={2}>
        {scenarios.map((scenario) => (
          <Grid item xs={12} md={4} key={scenario.id}>
            <Card>
              <CardActionArea onClick={() => onSelect(scenario.id)}>
                <CardContent>
                  <Typography variant="h6">
                    {scenario.name}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {scenario.description}
                  </Typography>
                </CardContent>
              </CardActionArea>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};
*/
```

### タスク9.3: 進捗表示コンポーネント
```typescript
// frontend/src/components/ProgressDisplay.tsx を作成
/*
import React from 'react';
import {
  Box,
  Typography,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
} from '@mui/material';

interface ProgressDisplayProps {
  currentStep: string;
  progress: number;
  logs: string[];
}

const steps = [
  { id: 'scraping', label: 'コンテンツ取得中' },
  { id: 'summarizing', label: '要約生成中' },
  { id: 'script', label: '台本作成中' },
  { id: 'voice', label: '音声生成中' },
  { id: 'subtitle', label: '字幕作成中' },
];

export const ProgressDisplay: React.FC<ProgressDisplayProps> = ({
  currentStep,
  progress,
  logs,
}) => {
  return (
    <Box sx={{ mt: 4 }}>
      <Typography variant="h4" gutterBottom>
        処理中...
      </Typography>
      
      <LinearProgress
        variant="determinate"
        value={progress}
        sx={{ mb: 4 }}
      />
      
      <List>
        {steps.map((step, index) => (
          <ListItem key={step.id}>
            <ListItemText
              primary={step.label}
              primaryTypographyProps={{
                color: currentStep === step.id ? 'primary' : 'text.secondary',
                fontWeight: currentStep === step.id ? 'bold' : 'normal',
              }}
            />
          </ListItem>
        ))}
      </List>
      
      {logs.length > 0 && (
        <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
          <Typography variant="body2" component="pre">
            {logs.join('\n')}
          </Typography>
        </Box>
      )}
    </Box>
  );
};
*/
```

### タスク9.4: 結果表示コンポーネント
```typescript
// frontend/src/components/ResultViewer.tsx を作成
/*
import React from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
} from '@mui/material';
import { Download } from '@mui/icons-material';
import { GeneratedFile } from '../types';

interface ResultViewerProps {
  projectId: string;
  files: GeneratedFile[];
}

export const ResultViewer: React.FC<ResultViewerProps> = ({
  projectId,
  files,
}) => {
  const handleDownload = (file: GeneratedFile) => {
    window.open(file.downloadUrl, '_blank');
  };

  return (
    <Box sx={{ mt: 4 }}>
      <Typography variant="h4" gutterBottom>
        生成完了！
      </Typography>
      
      <Grid container spacing={2}>
        {files.map((file) => (
          <Grid item xs={12} md={6} key={file.type}>
            <Card>
              <CardContent>
                <Typography variant="h6">
                  {file.name}
                </Typography>
                <Button
                  startIcon={<Download />}
                  onClick={() => handleDownload(file)}
                  sx={{ mt: 2 }}
                >
                  ダウンロード
                </Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};
*/
```

## フェーズ10: 統合・テスト（Day 17-18）

### タスク10.1: メインApp実装
```typescript
// frontend/src/App.tsx を更新
/*
import React, { useState } from 'react';
import { Container, CssBaseline } from '@mui/material';
import { QueryClient, QueryClientProvider } from 'react-query';
import { UrlInput } from './components/UrlInput';
import { ScenarioSelector } from './components/ScenarioSelector';
import { ProgressDisplay } from './components/ProgressDisplay';
import { ResultViewer } from './components/ResultViewer';
import { projectAPI, generationAPI } from './services/api';

const queryClient = new QueryClient();

type AppState = 'url' | 'scenario' | 'processing' | 'result';

function App() {
  const [state, setState] = useState<AppState>('url');
  const [projectId, setProjectId] = useState<string>('');
  const [url, setUrl] = useState<string>('');

  // 実装詳細...

  return (
    <QueryClientProvider client={queryClient}>
      <CssBaseline />
      <Container maxWidth="md">
        {/* 各状態に応じたコンポーネントを表示 */}
      </Container>
    </QueryClientProvider>
  );
}

export default App;
*/
```

### タスク10.2: エンドツーエンドテスト
```python
# backend/tests/test_integration.py を作成
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_full_process():
    # 1. プロジェクト作成
    response = client.post("/api/projects", json={
        "url": "https://example.com",
        "scenario_type": "product_introduction"
    })
    assert response.status_code == 200
    project_id = response.json()["project_id"]
    
    # 2. 処理開始
    response = client.post(f"/api/generate/process?project_id={project_id}")
    assert response.status_code == 200
    
    # 3. ステータス確認
    response = client.get(f"/api/projects/{project_id}/status")
    assert response.status_code == 200
    
    # 実際の処理は非同期なので、適切な待機処理を追加

def test_invalid_url():
    response = client.post("/api/projects", json={
        "url": "invalid-url",
        "scenario_type": "product_introduction"
    })
    # URLバリデーションのテスト
"""
```

## フェーズ11: 最適化・ドキュメント（Day 19-20）

### タスク11.1: エラーハンドリング強化
```python
# backend/app/utils/errors.py を作成
"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class AppError(Exception):
    def __init__(self, code: str, message: str, details: Dict[str, Any] = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)

def handle_error(error: Exception, project_id: str = None):
    logger.error(f"Error in project {project_id}: {str(error)}")
    
    if isinstance(error, AppError):
        return {
            "error": error.code,
            "message": error.message,
            "details": error.details
        }
    
    return {
        "error": "E999",
        "message": "予期しないエラーが発生しました",
        "details": {"original_error": str(error)}
    }
"""
```

### タスク11.2: デプロイメントガイド
```markdown
# デプロイメントガイド を作成

## 必要な環境
- Python 3.9+
- Node.js 16+
- Chrome/Chromium (Selenium用)

## バックエンドのデプロイ

1. 依存関係のインストール
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. 環境変数の設定
   ```bash
   cp .env.example .env
   # .envファイルを編集してAPIキーを設定
   ```

3. サーバー起動
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8080
   ```

## フロントエンドのデプロイ

1. 依存関係のインストール
   ```bash
   cd frontend
   npm install
   ```

2. ビルド
   ```bash
   npm run build
   ```

3. 配信
   ```bash
   npm install -g serve
   serve -s build -l 3000
   ```

## Dockerを使用したデプロイ

Dockerfile例:
```dockerfile
# backend/Dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```
```

## デバッグ用コマンド
```bash
# バックエンド起動（開発モード）
cd backend
uvicorn app.main:app --reload --port 8080

# フロントエンド起動（開発モード）
cd frontend
npm start

# ログ確認
tail -f backend/logs/app.log

# テスト実行
cd backend
pytest tests/

cd frontend
npm test
```

この実行計画書に従って、各フェーズを順番に実装していくことで、システムを完成させることができます。各タスクは独立して実装可能で、AIに指示を出す際は該当するタスクのコードブロックをコピーして使用できます。