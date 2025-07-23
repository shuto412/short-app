from typing import Dict, List, Optional
import yaml
import json
import logging
from datetime import datetime
from app.models.script import Script, Scene, VoiceSettings, ScriptMetadata

logger = logging.getLogger(__name__)

class ScriptGenerator:
    def __init__(self, claude_client):
        self.claude = claude_client
        self.default_voice_settings = VoiceSettings()
    
    async def generate(self, summary: str, scenario_type: str, target_duration: int = 60, title: Optional[str] = None) -> Dict:
        """
        台本を生成
        
        Args:
            summary: コンテンツの要約
            scenario_type: シナリオタイプ
            target_duration: 目標時間（秒）
            title: タイトル（省略時は自動生成）
            
        Returns:
            生成された台本データ
        """
        try:
            logger.info(f"Starting script generation for scenario: {scenario_type}")
            
            # テンプレート読み込み
            template = self._load_template(scenario_type)
            
            # タイトル生成（未指定の場合）
            if not title:
                if self.claude:
                    title = await self.claude.generate_title(summary)
                else:
                    title = self._generate_fallback_title(summary, scenario_type)
            
            # 台本生成プロンプト作成
            prompt = self._create_generation_prompt(summary, template, target_duration)
            
            # Claude APIで台本生成（利用できない場合はフォールバック）
            if self.claude:
                script_content = await self._generate_with_claude(prompt)
            else:
                logger.warning("Claude API not available, using fallback script generation")
                script_content = self._generate_fallback_script_content(summary, template, target_duration)
            
            # 台本データを構造化
            structured_script = self._structure_script_data(
                script_content, scenario_type, target_duration, title
            )
            
            logger.info(f"Successfully generated script with {len(structured_script['scenes'])} scenes")
            return structured_script
            
        except Exception as e:
            logger.error(f"Script generation failed: {str(e)}")
            raise Exception(f"Failed to generate script: {str(e)}")
    
    def _load_template(self, scenario_type: str) -> Dict:
        """シナリオテンプレートを読み込み"""
        templates = {
            "product_introduction": {
                "name": "製品紹介",
                "structure": [
                    {"section": "opening", "name": "オープニング", "duration_ratio": 0.15},
                    {"section": "problem", "name": "課題提示", "duration_ratio": 0.25},
                    {"section": "solution", "name": "解決策", "duration_ratio": 0.45},
                    {"section": "cta", "name": "行動喚起", "duration_ratio": 0.15}
                ],
                "voice_settings": {"emotion": "confident", "speed": 1.0}
            },
            "tutorial": {
                "name": "チュートリアル",
                "structure": [
                    {"section": "intro", "name": "導入", "duration_ratio": 0.1},
                    {"section": "overview", "name": "概要説明", "duration_ratio": 0.2},
                    {"section": "steps", "name": "手順説明", "duration_ratio": 0.6},
                    {"section": "conclusion", "name": "まとめ", "duration_ratio": 0.1}
                ],
                "voice_settings": {"emotion": "friendly", "speed": 0.95}
            },
            "feature_explanation": {
                "name": "機能説明",
                "structure": [
                    {"section": "intro", "name": "導入", "duration_ratio": 0.2},
                    {"section": "features", "name": "機能詳細", "duration_ratio": 0.6},
                    {"section": "benefits", "name": "利点・効果", "duration_ratio": 0.2}
                ],
                "voice_settings": {"emotion": "informative", "speed": 1.0}
            }
        }
        
        return templates.get(scenario_type, templates["product_introduction"])
    
    def _create_generation_prompt(self, summary: str, template: Dict, target_duration: int) -> str:
        """台本生成用プロンプトを作成"""
        structure_info = "\n".join([
            f"- {section['name']} ({int(section['duration_ratio'] * target_duration)}秒): {section['section']}"
            for section in template['structure']
        ])
        
        prompt = f'''以下の要約から{target_duration}秒の動画台本を生成してください。

シナリオタイプ: {template['name']}
構成:
{structure_info}

要約:
{summary}

以下の要件に従って台本を作成してください:

1. 自然で聞きやすい日本語
2. 動画視聴者に向けた親しみやすい語りかけ
3. 指定された時間配分に従った構成
4. 各セクションに適切な感情やトーンの指定

以下のJSON形式で出力してください:
{{
    "scenes": [
        {{
            "scene_id": 1,
            "scene_type": "opening",
            "duration": 9.0,
            "text": "こんにちは！今日は素晴らしい製品をご紹介します。",
            "voice_settings": {{
                "emotion": "cheerful",
                "speed": 1.0,
                "pitch": 1.0
            }}
        }}
    ]
}}'''
        
        return prompt
    
    async def _generate_with_claude(self, prompt: str) -> str:
        """Claude APIで台本生成"""
        message = self.claude.client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return message.content[0].text
    
    def _structure_script_data(self, script_content: str, scenario_type: str, target_duration: int, title: str) -> Dict:
        """台本データを構造化"""
        try:
            # JSON部分を抽出
            script_json = self._extract_json_from_response(script_content)
            
            # メタデータ作成
            metadata = {
                "project_id": "",  # 後で設定
                "title": title,
                "scenario_type": scenario_type,
                "total_duration": target_duration,
                "created_at": datetime.now().isoformat()
            }
            
            # シーンデータの検証と補正
            scenes = script_json.get("scenes", [])
            validated_scenes = self._validate_and_fix_scenes(scenes, target_duration)
            
            return {
                "metadata": metadata,
                "scenes": validated_scenes
            }
            
        except Exception as e:
            logger.warning(f"Failed to parse generated script, creating fallback: {str(e)}")
            return self._create_fallback_script(scenario_type, target_duration, title)
    
    def _extract_json_from_response(self, response: str) -> Dict:
        """レスポンスからJSON部分を抽出"""
        import json
        import re
        
        # JSONブロックを探す
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            return json.loads(json_str)
        else:
            raise ValueError("No valid JSON found in response")
    
    def _validate_and_fix_scenes(self, scenes: List[Dict], target_duration: int) -> List[Dict]:
        """シーンデータの検証と補正"""
        if not scenes:
            return self._create_default_scenes(target_duration)
        
        validated_scenes = []
        total_assigned_duration = 0
        
        for i, scene in enumerate(scenes):
            validated_scene = {
                "scene_id": i + 1,
                "scene_type": scene.get("scene_type", "content"),
                "duration": float(scene.get("duration", 10.0)),
                "text": scene.get("text", "こちらのコンテンツをご紹介します。"),
                "voice_settings": scene.get("voice_settings", {
                    "emotion": "neutral",
                    "speed": 1.0,
                    "pitch": 1.0
                })
            }
            
            validated_scenes.append(validated_scene)
            total_assigned_duration += validated_scene["duration"]
        
        # 時間の調整
        if total_assigned_duration != target_duration:
            self._adjust_scene_durations(validated_scenes, target_duration)
        
        return validated_scenes
    
    def _adjust_scene_durations(self, scenes: List[Dict], target_duration: int):
        """シーンの時間を目標時間に調整"""
        current_total = sum(scene["duration"] for scene in scenes)
        if current_total == 0:
            return
        
        ratio = target_duration / current_total
        for scene in scenes:
            scene["duration"] = round(scene["duration"] * ratio, 1)
    
    def _create_default_scenes(self, target_duration: int) -> List[Dict]:
        """デフォルトシーンを作成"""
        return [
            {
                "scene_id": 1,
                "scene_type": "opening",
                "duration": target_duration * 0.3,
                "text": "こんにちは！本日はご視聴いただき、ありがとうございます。",
                "voice_settings": {"emotion": "cheerful", "speed": 1.0, "pitch": 1.0}
            },
            {
                "scene_id": 2,
                "scene_type": "main",
                "duration": target_duration * 0.5,
                "text": "こちらの内容について詳しくご説明いたします。",
                "voice_settings": {"emotion": "informative", "speed": 1.0, "pitch": 1.0}
            },
            {
                "scene_id": 3,
                "scene_type": "closing",
                "duration": target_duration * 0.2,
                "text": "ご視聴いただき、ありがとうございました。",
                "voice_settings": {"emotion": "grateful", "speed": 1.0, "pitch": 1.0}
            }
        ]
    
    def _create_fallback_script(self, scenario_type: str, target_duration: int, title: str) -> Dict:
        """フォールバック台本を作成"""
        metadata = {
            "project_id": "",
            "title": title,
            "scenario_type": scenario_type,
            "total_duration": target_duration,
            "created_at": datetime.now().isoformat()
        }
        
        scenes = self._create_default_scenes(target_duration)
        
        return {
            "metadata": metadata,
            "scenes": scenes
        }
    
    def _generate_fallback_title(self, summary: str, scenario_type: str) -> str:
        """フォールバックタイトルを生成"""
        scenario_names = {
            "product_introduction": "製品紹介",
            "tutorial": "使い方ガイド",
            "feature_explanation": "機能説明"
        }
        
        # 要約から短いキーワードを抽出
        words = summary.split()[:3]  # 最初の3単語を使用
        keyword = " ".join(words)[:10] if words else "コンテンツ"
        
        base_name = scenario_names.get(scenario_type, "動画")
        return f"{keyword} - {base_name}"
    
    def _generate_fallback_script_content(self, summary: str, template: Dict, target_duration: int) -> str:
        """フォールバック台本コンテンツを生成"""
        # テンプレート構造に基づいてシンプルな台本を生成
        scenes = []
        current_time = 0
        
        for i, section in enumerate(template['structure']):
            duration = section['duration_ratio'] * target_duration
            
            # セクションに応じたデフォルトテキスト
            if section['section'] == 'opening':
                text = "こんにちは！本日はご視聴いただき、ありがとうございます。"
            elif section['section'] == 'problem':
                text = "まず、解決すべき課題について説明いたします。"
            elif section['section'] == 'solution':
                text = "この内容について詳しくご紹介いたします。"
            elif section['section'] == 'cta':
                text = "ご視聴いただき、ありがとうございました。"
            else:
                text = f"{section['name']}について説明いたします。"
            
            scene = {
                "scene_id": i + 1,
                "scene_type": section['section'],
                "duration": round(duration, 1),
                "text": text,
                "voice_settings": {
                    "emotion": "neutral",
                    "speed": 1.0,
                    "pitch": 1.0
                }
            }
            scenes.append(scene)
        
        # JSONとして返す
        import json
        return json.dumps({"scenes": scenes}, ensure_ascii=False, indent=2)
