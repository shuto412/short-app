from typing import Dict, List, Optional
import yaml
import json
import logging
import os
from datetime import datetime
from app.models.script import Script, Scene, VoiceSettings, ScriptMetadata

logger = logging.getLogger(__name__)

class ScriptGenerator:
    def __init__(self, claude_client):
        self.claude = claude_client
        self.default_voice_settings = VoiceSettings()
        # テンプレートディレクトリのパスを設定
        self.template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "template_scenario")
        # 許可シーンタイプ
        self.allowed_scene_types = {
            "opening",
            "main_content",
            "explanation",
            "demonstration",
            "conclusion",
            "cta",
        }
    
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
            
            # summary.yamlからデータを抽出してテンプレート変数を置換
            summary_data = self._parse_summary_yaml(summary)
            template = self._replace_template_variables(template, summary_data)
            
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
        """シナリオテンプレートをYAMLファイルから読み込み"""
        try:
            template_file = os.path.join(self.template_dir, f"{scenario_type}.yaml")
            
            # テンプレートファイルが存在するかチェック
            if not os.path.exists(template_file):
                logger.warning(f"Template file not found: {template_file}, using default")
                return self._get_default_template()
            
            # YAMLファイルを読み込み
            with open(template_file, 'r', encoding='utf-8') as f:
                template = yaml.safe_load(f)
            
            # テンプレートの妥当性をチェック
            if not self._validate_template(template):
                logger.warning(f"Invalid template format in {template_file}, using default")
                return self._get_default_template()
            
            logger.info(f"Successfully loaded template: {scenario_type}")
            return template
            
        except Exception as e:
            logger.error(f"Failed to load template {scenario_type}: {str(e)}")
            return self._get_default_template()
    
    def _validate_template(self, template: Dict) -> bool:
        """テンプレートの妥当性をチェック"""
        required_fields = ['name', 'structure', 'voice_settings']
        
        # 必須フィールドのチェック
        for field in required_fields:
            if field not in template:
                return False
        
        # 構造の妥当性チェック
        if not isinstance(template['structure'], list):
            return False
        
        for section in template['structure']:
            if not all(key in section for key in ['section', 'name', 'duration_ratio']):
                return False
            if not isinstance(section['duration_ratio'], (int, float)):
                return False
        
        # 時間配分の合計が1.0に近いかチェック
        total_ratio = sum(section['duration_ratio'] for section in template['structure'])
        if abs(total_ratio - 1.0) > 0.1:  # 10%の誤差を許容
            logger.warning(f"Template duration ratios sum to {total_ratio}, expected ~1.0")
        
        return True
    
    def _get_default_template(self) -> Dict:
        """デフォルトテンプレートを返す"""
        return {
            "name": "基本構成",
            "structure": [
                {"section": "opening", "name": "オープニング", "duration_ratio": 0.2},
                {"section": "main_content", "name": "メイン", "duration_ratio": 0.6},
                {"section": "conclusion", "name": "クロージング", "duration_ratio": 0.2}
            ],
            "voice_settings": {"emotion": "neutral", "speed": 1.0, "pitch": 1.0, "volume": 1.0}
        }

    def _normalize_scene_type(self, raw_type: str) -> str:
        """テンプレートや生成結果のシーンタイプを設計上の許可値に正規化"""
        if not raw_type:
            return "main_content"
        t = str(raw_type).lower().strip()
        mapping = {
            "main": "main_content",
            "content": "main_content",
            "problem": "explanation",
            "solution": "demonstration",
            "closing": "conclusion",
            "end": "conclusion",
        }
        normalized = mapping.get(t, t)
        return normalized if normalized in self.allowed_scene_types else "main_content"
    
    def get_available_templates(self) -> Dict:
        """利用可能なテンプレート一覧を取得"""
        try:
            index_file = os.path.join(self.template_dir, "index.yaml")
            
            if not os.path.exists(index_file):
                # index.yamlがない場合は、ディレクトリからテンプレートを検索
                templates = {}
                if os.path.exists(self.template_dir):
                    for file in os.listdir(self.template_dir):
                        if file.endswith('.yaml') and file != 'index.yaml':
                            template_id = file[:-5]  # .yamlを除去
                            templates[template_id] = {
                                "file": file,
                                "category": "その他",
                                "tags": []
                            }
                return {"templates": templates}
            
            with open(index_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
                
        except Exception as e:
            logger.error(f"Failed to load template index: {str(e)}")
            return {"templates": {}}
    
    def _create_generation_prompt(self, summary: str, template: Dict, target_duration: int) -> str:
        """台本生成用プロンプトを作成"""
        # テンプレートの詳細情報を含める
        template_description = template.get('description', '')
        
        # 各セクションの詳細説明を含める（変数置換後の内容）
        structure_info = "\n".join([
            f"- {section['name']} ({int(section['duration_ratio'] * target_duration)}秒): {section['section']}\n"
            f"  詳細: {section.get('description', '詳細説明なし')}"
            for section in template['structure']
        ])
        
        # 音声設定情報も含める
        voice_settings = template.get('voice_settings', {})
        voice_info = f"""
音声設定:
- 感情: {voice_settings.get('emotion', 'neutral')}
- 速度: {voice_settings.get('speed', 1.0)}
- ピッチ: {voice_settings.get('pitch', 1.0)}
- 音量: {voice_settings.get('volume', 1.0)}
"""
        
        # 最初のセクションの説明をサンプルテキストとして使用
        first_section = template['structure'][0] if template['structure'] else {}
        sample_text = first_section.get('description', '製品をご紹介します')
        sample_text_jp = self._convert_to_hiragana(sample_text)
        
        prompt = f'''以下の要約から{target_duration}秒の動画台本を生成してください。

シナリオタイプ: {template['name']}
テンプレート説明: {template_description}

構成と詳細:
{structure_info}

{voice_info}

要約:
{summary}

以下の要件に従って台本を作成してください:

1. 自然で聞きやすい日本語
2. 動画視聴者に向けた親しみやすい語りかけ
3. 指定された時間配分に従った構成
4. 各セクションの詳細説明に基づいた内容（上記の詳細説明を参考にすること）
5. 指定された音声設定に適した感情やトーン
6. 要約から具体的な製品名やサービス名を抽出し、各セクションで適切に使用すること
7. 各シーンは text（原文）と text_jp（原文のひらがな表記）の両方を含めること
8. text_jp は必ず全てひらがなで出力すること（漢字・カタカナ・英語・数字を含めない）、text_jp は音声生成AIへプロンプトとして送られる文章なので、textのよみがなをひらがなで出力すること

以下の様なJSON形式で出力してください:
{{
    "scenes": [
        {{
            "scene_id": 1,
            "scene_type": "{first_section.get('section', 'opening')}",
            "duration": {int(first_section.get('duration_ratio', 0.2) * target_duration)},
            "text": "{sample_text}",
            "text_jp": "{sample_text_jp}",
            "voice_settings": {{
                "emotion": "{voice_settings.get('emotion', 'neutral')}",
                "speed": {voice_settings.get('speed', 1.0)},
                "pitch": {voice_settings.get('pitch', 1.0)}
            }}
        }}
    ]
}}

注意: 上記の詳細説明に含まれる具体的な製品名や機能名を必ず使用してください。'''
        
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
        from app.modules.kana_converter import to_hiragana

        for i, scene in enumerate(scenes):
            base_text = scene.get("text", "こちらのコンテンツをご紹介します。")
            validated_scene = {
                "scene_id": i + 1,
                "scene_type": self._normalize_scene_type(scene.get("scene_type", "main_content")),
                "duration": float(scene.get("duration", 10.0)),
                "text": base_text,
                "text_jp": scene.get("text_jp") or to_hiragana(base_text),
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
        from app.modules.kana_converter import to_hiragana
        return [
            {
                "scene_id": 1,
                "scene_type": "opening",
                "duration": target_duration * 0.3,
                "text": "こんにちは！本日はご視聴いただき、ありがとうございます。",
                "text_jp": to_hiragana("こんにちは！本日はご視聴いただき、ありがとうございます。"),
                "voice_settings": {"emotion": "cheerful", "speed": 1.0, "pitch": 1.0}
            },
            {
                "scene_id": 2,
                "scene_type": "main_content",
                "duration": target_duration * 0.5,
                "text": "こちらの内容について詳しくご説明いたします。",
                "text_jp": to_hiragana("こちらの内容について詳しくご説明いたします。"),
                "voice_settings": {"emotion": "informative", "speed": 1.0, "pitch": 1.0}
            },
            {
                "scene_id": 3,
                "scene_type": "conclusion",
                "duration": target_duration * 0.2,
                "text": "ご視聴いただき、ありがとうございました。",
                "text_jp": to_hiragana("ご視聴いただき、ありがとうございました。"),
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
        
        from app.modules.kana_converter import to_hiragana

        for i, section in enumerate(template['structure']):
            duration = section['duration_ratio'] * target_duration
            
            # セクションに応じたデフォルトテキスト
            section_key = str(section['section']).lower()
            if section_key == 'opening':
                text = "こんにちは！本日はご視聴いただき、ありがとうございます。"
            elif section_key == 'problem':
                text = "まず、解決すべき課題について説明いたします。"
            elif section_key == 'solution':
                text = "この内容について詳しくご紹介いたします。"
            elif section_key == 'cta':
                text = "ご視聴いただき、ありがとうございました。"
            else:
                text = f"{section['name']}について説明いたします。"
            
            normalized_type = self._normalize_scene_type(section_key)
            scene = {
                "scene_id": i + 1,
                "scene_type": normalized_type,
                "duration": round(duration, 1),
                "text": text,
                "text_jp": to_hiragana(text),
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

    def _replace_template_variables(self, template: Dict, summary_data: Dict) -> Dict:
        """テンプレート内の変数をsummary.yamlの値で置換"""
        try:
            # テンプレートをディープコピー
            import copy
            replaced_template = copy.deepcopy(template)
            
            # 利用可能な変数を定義
            variables = {
                'product_name': summary_data.get('product_info', {}).get('product_name', '製品'),
                'product_description': summary_data.get('product_info', {}).get('description', '製品の説明'),
                'price': self._format_price_info(summary_data.get('product_info', {}).get('price', [])),
                'features': self._format_features_info(summary_data.get('product_info', {}).get('specifications', {}).get('features', [])),
                'weight': summary_data.get('product_info', {}).get('specifications', {}).get('weight', '重量不明'),
                'dimensions': self._format_dimensions_info(summary_data.get('product_info', {}).get('specifications', {}).get('dimensions', {}))
            }
            
            # テンプレート内の変数を置換
            replaced_template = self._replace_variables_in_dict(replaced_template, variables)
            
            logger.info(f"Template variables replaced successfully")
            return replaced_template
            
        except Exception as e:
            logger.warning(f"Failed to replace template variables: {str(e)}, using original template")
            return template
    
    def _replace_variables_in_dict(self, data: any, variables: Dict) -> any:
        """辞書内の文字列に含まれる変数を置換"""
        if isinstance(data, dict):
            return {key: self._replace_variables_in_dict(value, variables) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._replace_variables_in_dict(item, variables) for item in data]
        elif isinstance(data, str):
            # 文字列内の変数を置換
            for var_name, var_value in variables.items():
                placeholder = f"{{{var_name}}}"
                if placeholder in data:
                    data = data.replace(placeholder, str(var_value))
            return data
        else:
            return data
    
    def _format_price_info(self, price_list: List[str]) -> str:
        """価格情報を整形"""
        if not price_list:
            return "価格不明"
        return "、".join(price_list)
    
    def _format_features_info(self, features: List[str]) -> str:
        """機能情報を整形"""
        if not features:
            return "機能詳細不明"
        return "、".join(features[:3])  # 最初の3つの機能のみ表示
    
    def _format_dimensions_info(self, dimensions: Dict) -> str:
        """寸法情報を整形"""
        if not dimensions:
            return "寸法不明"
        
        parts = []
        if 'length' in dimensions:
            parts.append(f"長さ{dimensions['length']}")
        if 'width' in dimensions:
            parts.append(f"幅{dimensions['width']}")
        if 'height' in dimensions:
            parts.append(f"高さ{dimensions['height']}")
        
        return "×".join(parts) if parts else "寸法不明"
    
    def _parse_summary_yaml(self, summary: str) -> Dict:
        """summary文字列をYAMLとして解析"""
        try:
            # summaryがYAML文字列の場合
            if summary.strip().startswith('metadata:'):
                return yaml.safe_load(summary)
            else:
                # プレーンテキストの場合は空の辞書を返す
                return {}
        except Exception as e:
            logger.warning(f"Failed to parse summary as YAML: {str(e)}")
            return {}
    
    def _convert_to_hiragana(self, text: str) -> str:
        """テキストをひらがなに変換（簡易版）"""
        # 基本的な変換ルール
        conversions = {
            'こんにちは': 'こんにちは',
            'マウスログ': 'まうすろぐ',
            '今回は': 'こんかいは',
            'をご紹介します': 'をごしょうかいします',
            '製品': 'せいひん',
            'について': 'について',
            '詳しく': 'くわしく',
            '説明': 'せつめい',
            '機能': 'きのう',
            '軽さ': 'かるさ',
            'サイズ感': 'さいずかん',
            '価格設定': 'かかくせってい',
            '情報': 'じょうほう',
            'サイト': 'さいと',
            '御覧ください': 'ごらんください',
            'Xlite CrazyLight Gaming Mouse': 'えっくすらいとくれいじーらいとげーみんぐまうす',
            '競技eスポーツ': 'きょうぎいーすぽーつ',
            '最適化': 'さいてきか',
            '軽量': 'けいりょう',
            'ゲーミングマウス': 'げーみんぐまうす',
            '人間工学': 'にんげんこうがく',
            'デザイン': 'でざいん',
            '長時間': 'ちょうじかん',
            'ゲームプレイ': 'げーむぷれい',
            '快適性': 'かいてきせい',
            '提供': 'ていきょう',
            '先進的': 'せんしんてき',
            '搭載': 'とうさい',
            '究極': 'きゅうきょく',
            '体験': 'たいけん',
            '実現': 'じつげん',
            '驚異的': 'きょういてき',
            '右利き用': 'みぎききよう',
            '形状': 'かたち',
            'XS-1': 'えっくすえすわん',
            'フラッグシップ': 'ふらっぐしっぷ',
            'センサー': 'せんさー',
            '最大': 'さいだい',
            '8K': 'はちけー',
            'ポーリングレート': 'ぽーりんぐれーと',
            '対応': 'たいおう',
            '1億回': 'いちおくかい',
            'クリック': 'くりっく',
            '耐久': 'たいきゅう',
            'Pulsar': 'ぱるさー',
            '光学': 'こうがく',
            'スイッチ': 'すいっち',
            '細かな': 'こまかな',
            'DPI': 'でぃーぴーあい',
            '設定': 'せってい',
            '可能': 'かのう',
            '軽量プラスチック': 'けいりょうぷらすちっく',
            'ケーブル': 'けーぶる',
            '別売り': 'べつうり',
            'ワイヤレス': 'わいやれす',
            'ドングル': 'どんぐる',
            'Size 1': 'さいずわん',
            'dot skates': 'どっとすけーつ',
            'regular skates': 'れぎゅらーすけーつ',
        }
        
        result = text
        for kanji, hiragana in conversions.items():
            result = result.replace(kanji, hiragana)
        
        return result
