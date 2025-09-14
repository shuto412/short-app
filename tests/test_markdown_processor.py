import asyncio
from app.modules.markdown_processor import MarkdownProcessor


def test_markdown_processor_basic():
    md = """---
title: サンプル
description: 説明
category: カテゴリ
tags: [a,b]
---
# 見出し
本文
"""

    proc = MarkdownProcessor()

    is_valid = asyncio.get_event_loop().run_until_complete(proc.validate_markdown(md, "sample.md"))
    assert is_valid is True

    meta = asyncio.get_event_loop().run_until_complete(proc.extract_metadata(md))
    assert meta["title"] == "サンプル"
    assert meta["description"] == "説明"
    assert meta["category"] == "カテゴリ"
    assert meta["tags"] == ["a", "b"]

    normalized = asyncio.get_event_loop().run_until_complete(proc.process_content(md))
    assert "# 見出し" in normalized and "---" not in normalized

    score = proc.estimate_content_quality(md)
    assert 0.0 <= score <= 100.0


def test_markdown_processor_invalid():
    md_bad = """---\n: bad\n---\ncontent"""
    proc = MarkdownProcessor()
    is_valid = asyncio.get_event_loop().run_until_complete(proc.validate_markdown(md_bad, "bad.md"))
    assert is_valid is False


