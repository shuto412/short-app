import re
import yaml
from typing import Dict, Optional


class MarkdownProcessor:
    async def validate_markdown(self, content: str, filename: Optional[str] = None) -> bool:
        if not isinstance(content, str) or len(content.strip()) == 0:
            return False
        fm = self._extract_front_matter(content)
        if fm is not None:
            try:
                yaml.safe_load(fm)
            except Exception:
                return False
        return True

    async def extract_metadata(self, content: str) -> Dict:
        defaults = {"title": None, "description": None, "category": None, "tags": []}
        fm = self._extract_front_matter(content)
        if fm is None:
            return defaults
        try:
            data = yaml.safe_load(fm) or {}
            return {
                "title": data.get("title"),
                "description": data.get("description"),
                "category": data.get("category"),
                "tags": data.get("tags", []) or [],
            }
        except Exception:
            return defaults

    async def process_content(self, content: str) -> str:
        body = self._remove_front_matter(content)
        lines = [re.sub(r"\s+$", "", line) for line in body.splitlines()]
        normalized = []
        blank = False
        for line in lines:
            if line.strip() == "":
                if not blank:
                    normalized.append("")
                blank = True
            else:
                normalized.append(line)
                blank = False
        return "\n".join(normalized).strip()

    def estimate_content_quality(self, content: str) -> float:
        score = 0
        text = self._remove_front_matter(content)
        length = len(re.sub(r"\s", "", text))
        if length >= 500:
            score += 40
        elif length >= 300:
            score += 25
        elif length >= 150:
            score += 10
        headings = len(re.findall(r"^#{1,6}\s+", text, flags=re.MULTILINE))
        score += min(30, headings * 6)
        has_fm = self._extract_front_matter(content) is not None
        score += 20 if has_fm else 0
        bullets = len(re.findall(r"^\s*[-*+]\s+", text, flags=re.MULTILINE))
        score += min(10, bullets * 2)
        return float(max(0, min(100, score)))

    def _extract_front_matter(self, content: str) -> Optional[str]:
        match = re.match(r"^---\n([\s\S]*?)\n---\n", content)
        if match:
            return match.group(1)
        return None

    def _remove_front_matter(self, content: str) -> str:
        return re.sub(r"^---\n([\s\S]*?)\n---\n", "", content, count=1)


