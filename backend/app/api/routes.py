"""API routes for resume analysis."""

from __future__ import annotations

import logging
import hashlib

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.cache import cache
from app.config import settings
from app.models.schemas import (
    HealthResponse,
    JobKeywordResponse,
    MatchRequest,
    MatchResponse,
    ResumeParseResponse,
    ResumeInfo,
)
from app.services.matcher import compute_match, extract_keywords, parse_resume
from app.services.pdf_parser import extract_text_from_pdf

logger = logging.getLogger(__name__)

router = APIRouter()


async def _run_match(resume_id: str, job_description: str) -> MatchResponse:
    """Match a previously parsed resume against a job description."""
    if not job_description.strip():
        raise HTTPException(status_code=400, detail="岗位描述不能为空")

    record = await cache.get("resume_record", resume_id)
    if not record:
        raise HTTPException(status_code=404, detail="未找到已解析的简历，请先上传并解析简历")

    raw_text = record.get("raw_text", "")
    resume = ResumeInfo(**record.get("resume", {}))

    keywords, summary = await extract_keywords(job_description)
    match_result = await compute_match(raw_text, resume, job_description, keywords)
    if not match_result:
        return MatchResponse(
            success=False,
            resume_id=resume_id,
            job_keywords=keywords,
            job_summary=summary,
            error="简历匹配评分失败，请稍后重试",
        )

    return MatchResponse(
        success=True,
        resume_id=resume_id,
        job_keywords=keywords,
        job_summary=summary,
        match=match_result,
    )


@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health():
    """Health check endpoint."""
    return HealthResponse(redis_available=cache.is_available)


@router.post("/resume/parse", response_model=ResumeParseResponse, tags=["Resume"])
async def parse_resume_endpoint(
    file: UploadFile = File(..., description="PDF 简历文件"),
    job_description: str = Form(None, description="岗位描述（可选）"),
):
    """Upload and parse a PDF resume. Optionally provide a job description for matching."""
    # --- Validate file ---
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="仅支持 PDF 格式文件")

    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件大小超过限制（最大 10 MB）")

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="上传文件为空")

    resume_id = hashlib.sha256(content).hexdigest()[:32]
    cached_record = await cache.get("resume_record", resume_id)
    if cached_record:
        resp = ResumeParseResponse(
            success=True,
            resume_id=resume_id,
            resume=ResumeInfo(**cached_record.get("resume", {})),
            raw_text=cached_record.get("raw_text", "")[:500],
        )
        if job_description and job_description.strip():
            match_resp = await _run_match(resume_id, job_description)
            resp.match = match_resp.match
        return resp

    # --- Parse PDF ---
    raw_text = extract_text_from_pdf(content)
    if not raw_text.strip():
        return ResumeParseResponse(success=False, error="无法从 PDF 中提取文本，请确认文件内容可复制")

    # --- Structure resume with AI ---
    resume_info = await parse_resume(raw_text)
    if resume_info is None:
        return ResumeParseResponse(
            success=False, resume_id=resume_id, raw_text=raw_text, error="简历解析失败，请检查文件内容"
        )

    await cache.set(
        "resume_record",
        resume_id,
        {"resume": resume_info.model_dump(), "raw_text": raw_text},
    )

    resp = ResumeParseResponse(
        success=True,
        resume_id=resume_id,
        resume=resume_info,
        raw_text=raw_text[:500],
    )

    # --- Optional: match against job description ---
    if job_description and job_description.strip():
        keywords, summary = await extract_keywords(job_description)
        match_result = await compute_match(raw_text, resume_info, job_description, keywords)
        if match_result:
            resp.match = match_result

    return resp


@router.post("/resume/match", response_model=MatchResponse, tags=["Resume"])
async def match_resume_endpoint(payload: MatchRequest):
    """Match an already parsed resume with a job description."""
    return await _run_match(payload.resume_id, payload.job_description)


@router.post("/job/keywords", response_model=JobKeywordResponse, tags=["Job"])
async def extract_job_keywords_endpoint(job_description: str = Form(...)):
    """Extract keywords from a job description."""
    if not job_description.strip():
        raise HTTPException(status_code=400, detail="岗位描述不能为空")

    keywords, summary = await extract_keywords(job_description)
    return JobKeywordResponse(keywords=keywords, summary=summary)
