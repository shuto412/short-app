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
        """プロジェクトディレクトリを作成"""
        project_path = os.path.join(self.base_dir, project_id)
        os.makedirs(project_path, exist_ok=True)
        return project_path
    
    async def save_file(self, project_id: str, filename: str, content: Any):
        """ファイルを保存"""
        project_path = await self.create_project_dir(project_id)
        file_path = os.path.join(project_path, filename)
        
        if filename.endswith('.yaml') or filename.endswith('.yml'):
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(yaml.dump(content, allow_unicode=True, default_flow_style=False))
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
        """ファイルを読み込み"""
        file_path = os.path.join(self.base_dir, project_id, filename)
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {filename}")
        
        if filename.endswith('.yaml') or filename.endswith('.yml'):
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                return yaml.safe_load(content)
        elif filename.endswith('.json'):
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                return json.loads(content)
        elif filename.endswith(('.wav', '.mp3', '.mp4')):
            async with aiofiles.open(file_path, 'rb') as f:
                return await f.read()
        elif filename.endswith('.txt'):  # ← .txtファイルを明示的に処理
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                return await f.read()
        else:
            # その他のテキストファイル
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                return await f.read()
    
    def list_project_files(self, project_id: str) -> list:
        """プロジェクトのファイル一覧を取得"""
        project_path = os.path.join(self.base_dir, project_id)
        if os.path.exists(project_path):
            return os.listdir(project_path)
        return []
    
    def file_exists(self, project_id: str, filename: str) -> bool:
        """ファイルの存在確認"""
        file_path = os.path.join(self.base_dir, project_id, filename)
        return os.path.exists(file_path)
    
    def get_file_path(self, project_id: str, filename: str) -> str:
        """ファイルパスを取得"""
        return os.path.join(self.base_dir, project_id, filename)
    
    def delete_file(self, project_id: str, filename: str) -> bool:
        """ファイルを削除"""
        try:
            file_path = os.path.join(self.base_dir, project_id, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False
    
    def delete_project(self, project_id: str) -> bool:
        """プロジェクト全体を削除"""
        try:
            import shutil
            project_path = os.path.join(self.base_dir, project_id)
            if os.path.exists(project_path):
                shutil.rmtree(project_path)
                return True
            return False
        except Exception:
            return False
