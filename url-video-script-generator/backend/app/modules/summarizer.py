import anthropic
from typing import Dict, Optional
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class ClaudeClient:
    def __init__(self):
        if not settings.CLAUDE_API_KEY or settings.CLAUDE_API_KEY == "your_key_here":
            raise ValueError("CLAUDE_API_KEY is not properly configured")
        
        self.client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)
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
