from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

from app.modules.markdown_processor import MarkdownProcessor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/markdown", tags=["markdown"])
processor = MarkdownProcessor()


class MarkdownValidateRequest(BaseModel):
    content: str
    filename: Optional[str] = None


class MarkdownPreviewResponse(BaseModel):
    title: Optional[str]
    description: Optional[str]
    category: Optional[str]
    tags: list
    quality: float
    preview: str


@router.post("/validate")
async def validate_markdown(req: MarkdownValidateRequest):
    try:
        is_valid = await processor.validate_markdown(req.content, req.filename)
        return {"valid": is_valid}
    except Exception as e:
        logger.error(f"Markdown validate failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid markdown content")


@router.post("/preview", response_model=MarkdownPreviewResponse)
async def preview_markdown(req: MarkdownValidateRequest):
    try:
        valid = await processor.validate_markdown(req.content, req.filename)
        if not valid:
            raise HTTPException(status_code=400, detail="Markdown validation failed")

        meta = await processor.extract_metadata(req.content)
        quality = processor.estimate_content_quality(req.content)
        normalized = await processor.process_content(req.content)

        preview_text = normalized[:500]
        return {
            "title": meta.get("title"),
            "description": meta.get("description"),
            "category": meta.get("category"),
            "tags": meta.get("tags", []),
            "quality": quality,
            "preview": preview_text,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Markdown preview failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to preview markdown")


