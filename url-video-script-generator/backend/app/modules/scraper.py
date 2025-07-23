import requests
from bs4 import BeautifulSoup
from typing import Optional
import logging
import asyncio
from urllib.parse import urljoin, urlparse

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

logger = logging.getLogger(__name__)

class Scraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    async def scrape(self, url: str, use_selenium: bool = False) -> str:
        """
        URLからコンテンツを取得
        - 静的サイト: BeautifulSoup使用
        - 動的サイト: Selenium使用
        - テキスト抽出と整形
        """
        try:
            logger.info(f"Starting scraping for URL: {url} (Selenium: {use_selenium})")
            
            if use_selenium:
                content = await self._scrape_with_selenium(url)
            else:
                content = await self._scrape_with_requests(url)
            
            logger.info(f"Successfully scraped {len(content)} characters from URL")
            return content
            
        except Exception as e:
            logger.error(f"Scraping failed for URL {url}: {str(e)}")
            # 静的スクレイピングが失敗した場合、Seleniumで再試行
            if not use_selenium:
                logger.info("Retrying with Selenium...")
                try:
                    return await self.scrape(url, use_selenium=True)
                except Exception as selenium_error:
                    logger.error(f"Selenium scraping also failed: {str(selenium_error)}")
            raise
    
    async def _scrape_with_requests(self, url: str) -> str:
        """RequestsとBeautifulSoupを使用した静的スクレイピング"""
        # 非同期でHTTPリクエストを実行
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, self._make_request, url)
        
        if response is None:
            raise Exception("Failed to fetch content from URL")
        
        # BeautifulSoupでHTMLを解析
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 不要な要素を削除
        self._remove_unwanted_elements(soup)
        
        # テキスト抽出
        text = self._extract_text(soup)
        
        # テキストを整形
        cleaned_text = self._clean_text(text)
        
        return cleaned_text
    
    async def _scrape_with_selenium(self, url: str) -> str:
        """Seleniumを使用した動的スクレイピング"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._selenium_scrape, url)
    
    def _selenium_scrape(self, url: str) -> str:
        """Seleniumでのスクレイピング処理"""
        driver = None
        try:
            driver = self._setup_driver()
            driver.get(url)
            
            # ページ読み込み待機
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # JavaScript実行後の少し待機
            driver.implicitly_wait(3)
            
            # ページソースを取得
            page_source = driver.page_source
            
            # BeautifulSoupで解析
            soup = BeautifulSoup(page_source, 'html.parser')
            self._remove_unwanted_elements(soup)
            text = self._extract_text(soup)
            cleaned_text = self._clean_text(text)
            
            return cleaned_text
            
        except (TimeoutException, WebDriverException) as e:
            logger.error(f"Selenium error: {str(e)}")
            raise Exception(f"Failed to scrape with Selenium: {str(e)}")
        finally:
            if driver:
                driver.quit()
    
    def _setup_driver(self) -> webdriver.Chrome:
        """Seleniumドライバーの設定"""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # User-Agentの設定
        options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        try:
            driver = webdriver.Chrome(options=options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return driver
        except Exception as e:
            logger.error(f"Failed to setup Chrome driver: {str(e)}")
            raise Exception("Chrome driver setup failed. Please ensure ChromeDriver is installed.")
    
    def _make_request(self, url: str) -> Optional[requests.Response]:
        """HTTPリクエストを実行"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.error(f"HTTP request failed: {str(e)}")
            return None
    
    def _remove_unwanted_elements(self, soup: BeautifulSoup) -> None:
        """不要な要素を削除"""
        # スクリプトとスタイルタグを削除
        for element in soup(["script", "style", "nav", "header", "footer", "aside"]):
            element.decompose()
        
        # コメントを削除
        from bs4 import Comment
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
    
    def _extract_text(self, soup: BeautifulSoup) -> str:
        """テキストを抽出"""
        # 主要なコンテンツ要素を優先的に取得
        content_selectors = [
            'main', 'article', '.content', '.post-content', 
            '.entry-content', '#content', '.main-content'
        ]
        
        content_text = ""
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                for element in elements:
                    content_text += element.get_text() + "\n"
                break
        
        # 主要コンテンツが見つからない場合は全体から取得
        if not content_text.strip():
            content_text = soup.get_text()
        
        return content_text
    
    def _clean_text(self, text: str) -> str:
        """テキストを整形"""
        # 行を分割してクリーンアップ
        lines = (line.strip() for line in text.splitlines())
        
        # 空行と短すぎる行を除去
        lines = [line for line in lines if line and len(line) > 3]
        
        # 重複する行を除去
        seen = set()
        unique_lines = []
        for line in lines:
            if line not in seen:
                seen.add(line)
                unique_lines.append(line)
        
        # テキストを結合
        cleaned_text = '\n'.join(unique_lines)
        
        # 連続する空白を整理
        import re
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
        cleaned_text = re.sub(r'\n\s*\n', '\n', cleaned_text)
        
        return cleaned_text.strip()
    
    def validate_url(self, url: str) -> bool:
        """URLの妥当性をチェック"""
        try:
            parsed = urlparse(url)
            return bool(parsed.netloc) and bool(parsed.scheme)
        except Exception:
            return False
    
    def detect_dynamic_content(self, url: str) -> bool:
        """動的コンテンツが必要かどうかを検出"""
        # 簡易判定：特定のドメインやパスパターンをチェック
        dynamic_indicators = [
            'spa', 'react', 'angular', 'vue', 'app',
            'javascript', 'ajax', 'api'
        ]
        
        url_lower = url.lower()
        return any(indicator in url_lower for indicator in dynamic_indicators)
