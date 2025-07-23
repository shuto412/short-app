#!/usr/bin/env python3

import asyncio
import sys
import os

# プロジェクトルートをPythonパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.modules.scraper import Scraper

async def test_scraper():
    """スクレイピングモジュールのテスト"""
    scraper = Scraper()
    
    # テスト用URL（静的サイト）
    test_urls = [
        "https://httpbin.org/html",  # シンプルなHTMLページ
        "https://example.com",       # 基本的なテストページ
    ]
    
    for url in test_urls:
        try:
            print(f"\n=== Testing URL: {url} ===")
            
            # URL妥当性チェック
            if not scraper.validate_url(url):
                print(f"❌ Invalid URL: {url}")
                continue
            
            # スクレイピング実行
            content = await scraper.scrape(url)
            
            print(f"✅ Successfully scraped {len(content)} characters")
            print(f"Content preview (first 200 chars):")
            print(content[:200] + "..." if len(content) > 200 else content)
            
        except Exception as e:
            print(f"❌ Error scraping {url}: {str(e)}")

if __name__ == "__main__":
    print("🔍 Testing Scraper Module")
    asyncio.run(test_scraper()) 