import anthropic
from typing import Dict, Optional
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class ClaudeClient:
    def __init__(self):
        if not settings.CLAUDE_API_KEY or settings.CLAUDE_API_KEY == "your_key_here":
            raise ValueError("CLAUDE_API_KEY is not properly configured")
        
        try:
            # Anthropic clientを初期化（明示的にパラメータを指定）
            self.client = anthropic.Anthropic(
                api_key=settings.CLAUDE_API_KEY,
                timeout=60.0,
                max_retries=2
            )
            logger.info("Successfully initialized Anthropic client")
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {str(e)}")
            raise ValueError(f"Claude client initialization failed: {str(e)}")
        self.max_tokens = 4000
    
    async def summarize(self, content: str, max_length: int = 500) -> str:
        """
        コンテンツを要約
        
        Args:
            content: 要約対象のコンテンツ
            max_length: 要約の最大文字数
            
        Returns:
            要約されたテキスト
        """
        try:
            logger.info(f"Starting summarization of {len(content)} characters")
            
            prompt = f'''以下のコンテンツを{max_length}文字以内で要約してください。
重要なポイントを箇条書きで抽出し、動画制作に役立つ情報を中心にまとめてください。

要約のポイント:
- 主要な内容・特徴
- 重要なメリット・利点
- 重要なメリット・利点にて解消される課題（重要なメリット・利点を説明するために解消される課題を記載）
- 特筆すべき機能や詳細
- ターゲットや用途

コンテンツ:
{content}

要約:'''
            
            message = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            
            summary = message.content[0].text
            logger.info(f"Successfully generated summary of {len(summary)} characters")
            return summary
            
        except Exception as e:
            logger.error(f"Summarization failed: {str(e)}")
            raise Exception(f"Failed to generate summary: {str(e)}")
    
    async def create_structured_summary(self, content: str) -> dict:
        """
        コンテンツから構造化された製品要約を生成
        
        Args:
            content: スクレイピングしたコンテンツ
            
        Returns:
            構造化された製品情報のディクショナリ
        """
        try:
            logger.info(f"Starting structured summarization of {len(content)} characters")
            
            prompt = f'''以下のコンテンツから製品情報を抽出し、下記の形式でYAMLとして出力してください。
コードブロック記法（```）は使用せず、直接YAMLを出力してください。

**重要な指示:**
1. コンテンツ内のすべての数値情報（寸法、重量、価格など）を漏らさず抽出してください
2. 製品名は正確に抽出し、カラーバリエーションも含めてください
3. 価格情報は単位も含めて正確に記載してください
4. 寸法情報は dimensions 内に詳細に分類してください
5. description には技術仕様ではなく、製品の特徴・利点・用途を記載してください

必須項目:
- product_name: 製品名（正確な製品名とカラーバリエーション）
- price: 価格情報（単位込み、複数価格がある場合は配列形式）
- specifications: 製品詳細（辞書形式）
  - size: サイズ表記（Size 1, Sサイズなど）
  - weight: 重さ情報（単位込み）
  - dimensions: 寸法の詳細情報（辞書形式）
    - length: 長さ（単位込み）
    - width: 幅（単位込み）
    - height: 高さ（単位込み）
  - materials: 素材・材質情報
  - features: 主な機能・特徴
  - other: その他の技術仕様
- description: 製品の特徴・利点・用途（技術仕様は含めず、魅力的な説明文として）

出力フォーマット例:
product_name: "X3 Mini Gaming Mouse"
price: 
  - "Black: 売り切れ"
  - "White: ¥14,960 JPY"
specifications:
  size: "ミニサイズ"
  weight: "50g (±1g)"
  dimensions:
    length: "4.7in (119.6mm)"
    width: "2.64in (67.1mm)"
    height: "1.61in (41mm)"
  materials: "軽量プラスチック"
  features:
    - "競技eスポーツ向け"
    - "高精度トラッキング"
  other: "ケーブル別売り"
description: "競技eスポーツに最適化された軽量50gのゲーミングマウス。コンパクトなミニサイズでありながら、高精度なトラッキング性能を実現。"

コンテンツ:
{content}

上記フォーマットに従って、コンテンツ内の全ての情報を漏らさずにYAMLを出力してください:'''

            message = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            
            yaml_text = message.content[0].text.strip()
            logger.info(f"Generated YAML text: {yaml_text[:200]}...")
            
            # デバッグ用：生成されたYAMLの完全な内容をログ出力
            logger.debug(f"Complete YAML response: {yaml_text}")
            
            # YAML解析を試行
            try:
                import yaml
                structured_data = yaml.safe_load(yaml_text)
                
                # 必須フィールドの存在確認と補完
                if not isinstance(structured_data, dict):
                    logger.warning("Invalid YAML structure, creating fallback")
                    raise ValueError("Invalid YAML structure")
                    
                # デフォルト値で補完
                default_summary = {
                    "product_name": structured_data.get("product_name", "製品名不明"),
                    "price": structured_data.get("price", "価格情報なし"),
                    "specifications": structured_data.get("specifications", {}),
                    "description": structured_data.get("description", "製品説明なし")
                }
                
                # specificationsの構造確認と補完
                if not isinstance(default_summary["specifications"], dict):
                    default_summary["specifications"] = {}
                
                # specifications内の必須フィールドを確認
                specs = default_summary["specifications"]
                if "dimensions" not in specs:
                    specs["dimensions"] = {}
                if not isinstance(specs["dimensions"], dict):
                    specs["dimensions"] = {}
                    
                logger.info(f"Successfully generated structured summary with product: {default_summary.get('product_name', 'Unknown')}")
                return default_summary
                
            except (yaml.YAMLError, ValueError) as e:
                logger.warning(f"YAML parsing failed, creating fallback structure: {str(e)}")
                logger.warning(f"Raw YAML text was: {yaml_text[:500]}")
                
                # フォールバック: より詳細な解析を試行
                # コンテンツから直接情報を抽出
                import re
                
                # 製品名の抽出（改善）
                product_name = "製品名抽出失敗"
                # 複数の製品名パターンを試行
                name_patterns = [
                    r'([A-Za-z0-9\s\-\_]+(?:gaming|mouse|マウス|ゲーミング)[A-Za-z0-9\s\-\_]*)',
                    r'([A-Za-z][A-Za-z0-9\s\-\_]{5,50})\s*(?:color|カラー|色)',
                    r'^([A-Za-z][A-Za-z0-9\s\-\_]{5,50})\s*(?:¥|\-)'
                ]
                for pattern in name_patterns:
                    match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
                    if match and match.group(1).strip():
                        product_name = match.group(1).strip()
                        break
                
                # 価格情報の抽出（改善）
                price_info = "価格情報抽出失敗"
                # より柔軟な価格パターン
                price_patterns = [
                    r'¥[\d,]+\s*JPY',  # ¥16,940 JPY
                    r'¥[\d,]+',        # ¥16,940
                    r'[\d,]+円',       # 16,940円
                    r'[\d,]+\s*yen'    # 16940 yen
                ]
                
                for pattern in price_patterns:
                    price_matches = re.findall(pattern, content, re.IGNORECASE)
                    if price_matches:
                        price_info = price_matches
                        break
                
                # 重量情報の抽出（改善）
                weight_info = "重量情報なし"
                weight_patterns = [
                    r'±?\s*(\d+(?:\.\d+)?g)(?:\s*\([^)]+\))?',  # ±41g (1.45oz)
                    r'(\d+(?:\.\d+)?\s*oz)',                    # 1.45oz
                    r'weight:\s*([^/\n]+)',                     # weight: 情報
                    r'重量[：:]\s*([^\n]+)'                      # 重量: 情報
                ]
                
                extracted_weights = []
                for pattern in weight_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    extracted_weights.extend(matches)
                
                if extracted_weights:
                    weight_info = " / ".join(set(extracted_weights))  # 重複除去
                
                # 寸法情報の抽出（改善）
                dimensions = {}
                dimension_patterns = {
                    'length': [r'length:\s*([\d.]+(?:in|mm)[^)]*(?:\([^)]+\))?)', r'長さ[：:]\s*([^\n]+)'],
                    'width': [r'width:\s*([\d.]+(?:in|mm)[^)]*(?:\([^)]+\))?)', r'幅[：:]\s*([^\n]+)'],
                    'height': [r'height:\s*([\d.]+(?:in|mm)[^)]*(?:\([^)]+\))?)', r'高さ[：:]\s*([^\n]+)']
                }
                
                for key, patterns in dimension_patterns.items():
                    for pattern in patterns:
                        match = re.search(pattern, content, re.IGNORECASE)
                        if match:
                            dimensions[key] = match.group(1).strip()
                            break
                
                # サイズ情報の抽出
                size_info = "サイズ情報なし"
                size_patterns = [
                    r'size\s+(\d+|[A-Z]+)',
                    r'サイズ[：:]\s*([^\n]+)',
                    r'(same\s+size[^.]+)',
                    r'(ミニサイズ|レギュラーサイズ|ラージサイズ)'
                ]
                
                for pattern in size_patterns:
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        size_info = match.group(1).strip()
                        break
                
                # 素材情報の抽出
                materials_info = "素材情報なし"
                material_patterns = [
                    r'(UHMW-PE|プラスチック|アルミニウム|カーボン)',
                    r'materials?[：:]\s*([^\n]+)',
                    r'素材[：:]\s*([^\n]+)'
                ]
                
                for pattern in material_patterns:
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        materials_info = match.group(1).strip()
                        break
                
                # 特徴・機能の抽出
                features = []
                feature_patterns = [
                    r'(\d+k\s*polling\s*rate)',
                    r'(\d+\s*dpi)',
                    r'(optical\s*switch)',
                    r'(wireless)',
                    r'(ergonomic)',
                    r'(lightweight|軽量)',
                    r'(gaming|ゲーミング)'
                ]
                
                for pattern in feature_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    features.extend(matches)
                
                # 重複除去と整理
                features = list(set([f.strip() for f in features if f.strip()]))
                
                return {
                    "product_name": product_name,
                    "price": price_info,
                    "specifications": {
                        "size": size_info,
                        "weight": weight_info,
                        "dimensions": dimensions,
                        "materials": materials_info,
                        "features": features,
                        "other": "その他仕様なし"
                    },
                    "description": content[:300] + "..." if len(content) > 300 else content
                }
                
        except Exception as e:
            logger.error(f"Structured summarization failed: {str(e)}")
            raise Exception(f"Failed to generate structured summary: {str(e)}")
    
    async def analyze_content_type(self, content: str) -> Dict[str, str]:
        """
        コンテンツのタイプを分析
        
        Args:
            content: 分析対象のコンテンツ
            
        Returns:
            コンテンツタイプの分析結果
        """
        try:
            prompt = f'''以下のコンテンツを分析して、適切な動画シナリオタイプを判定してください。

判定候補:
- product_introduction: 製品・サービスの紹介
- tutorial: 使い方・手順の説明
- feature_explanation: 特定機能の詳細説明
- company_overview: 会社・組織の紹介
- news_summary: ニュース・情報のまとめ

コンテンツ:
{content[:1000]}...

JSON形式で以下の情報を返してください:
{{
    "content_type": "判定したタイプ",
    "confidence": "信頼度（high/medium/low）",
    "reason": "判定理由",
    "suggested_duration": "推奨動画時間（秒）"
}}'''

            message = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            result = message.content[0].text
            logger.info(f"Content type analysis completed")
            
            # JSONパースを試行（失敗した場合はデフォルト値を返す）
            try:
                import json
                return json.loads(result)
            except json.JSONDecodeError:
                return {
                    "content_type": "product_introduction",
                    "confidence": "low",
                    "reason": "自動判定に失敗したため、デフォルトタイプを適用",
                    "suggested_duration": "60"
                }
                
        except Exception as e:
            logger.error(f"Content analysis failed: {str(e)}")
            return {
                "content_type": "product_introduction",
                "confidence": "low", 
                "reason": f"分析エラー: {str(e)}",
                "suggested_duration": "60"
            }
    
    async def generate_title(self, summary: str) -> str:
        """
        要約から魅力的なタイトルを生成
        
        Args:
            summary: 要約テキスト
            
        Returns:
            生成されたタイトル
        """
        try:
            prompt = f'''以下の要約から、動画のタイトルを生成してください。

要件:
- 20文字以内
- 魅力的で興味を引く
- 内容を適切に表現
- 日本語で自然な表現

要約:
{summary}

タイトル:'''

            message = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=100,
                messages=[{"role": "user", "content": prompt}]
            )
            
            title = message.content[0].text.strip()
            logger.info(f"Generated title: {title}")
            return title
            
        except Exception as e:
            logger.error(f"Title generation failed: {str(e)}")
            return "自動生成動画"
