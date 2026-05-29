"""PDF resume parsing service.

Supports PyMuPDF (fitz) as primary engine, with pdfplumber as fallback.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


def extract_text_from_pdf(content: bytes) -> str:
    """Extract and clean text from a PDF byte stream.

    Tries PyMuPDF first, falls back to pdfplumber.
    """
    text = _try_pymupdf(content)
    if text and text.strip():
        return _clean_text(text)

    text = _try_pdfplumber(content)
    if text and text.strip():
        return _clean_text(text)

    logger.warning("All PDF parsers returned empty text")
    return ""


def _try_pymupdf(content: bytes) -> Optional[str]:
    """Extract text with PyMuPDF (fitz)."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        logger.debug("PyMuPDF not available, skipping")
        return None

    try:
        doc = fitz.open(stream=content, filetype="pdf")
        pages = [page.get_text() for page in doc]
        doc.close()
        return "\n".join(pages)
    except Exception as exc:
        logger.warning("PyMuPDF extraction failed: %s", exc)
        return None


def _try_pdfplumber(content: bytes) -> Optional[str]:
    """Extract text with pdfplumber."""
    try:
        import pdfplumber
    except ImportError:
        logger.debug("pdfplumber not available, skipping")
        return None

    try:
        import io
        pages = []
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    pages.append(t)
        return "\n".join(pages)
    except Exception as exc:
        logger.warning("pdfplumber extraction failed: %s", exc)
        return None


def _clean_text(text: str) -> str:
    """Clean extracted text: normalize whitespace, remove noise."""
    # 替换零宽字符和控制字符
    text = re.sub(r"[​-‏ - ﻿]", "", text)
    # 统一换行：先合并软换行（非段落结束的换行）
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    # 多个空行压缩为一个
    text = re.sub(r"\n{3,}", "\n\n", text)
    # 去除首尾空白
    text = text.strip()
    return text
