"""Pydantic models for request/response schemas."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class MatchLevel(str, Enum):
    excellent = "excellent"
    good = "good"
    fair = "fair"
    poor = "poor"


class ResumeParseRequest(BaseModel):
    """请求参数 — 上传 PDF 后附加的岗位描述（可选）。"""
    job_description: Optional[str] = Field(
        None, description="岗位描述文本（可选）"
    )


class Education(BaseModel):
    degree: Optional[str] = None
    school: Optional[str] = None
    major: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class Project(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    description: Optional[str] = None
    tech_stack: Optional[str] = None
    highlights: Optional[str] = None


class ResumeInfo(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    job_intent: Optional[str] = None
    expected_salary: Optional[str] = None
    work_years: Optional[str] = None
    education: list[Education] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)


class MatchResult(BaseModel):
    score: int = Field(..., ge=0, le=100, description="匹配分数 0-100")
    level: MatchLevel = Field(..., description="匹配等级")
    skill_match_rate: float = Field(
        0, ge=0, le=1, description="技能匹配率 0-1"
    )
    experience_relevance: float = Field(
        0, ge=0, le=1, description="工作经验相关性 0-1"
    )
    project_relevance: float = Field(
        0, ge=0, le=1, description="项目经历相关性 0-1"
    )
    education_relevance: float = Field(
        0, ge=0, le=1, description="学历背景匹配度 0-1"
    )
    ai_score: float = Field(
        0, ge=0, le=1, description="AI 综合评分 0-1"
    )
    matched_keywords: list[str] = Field(
        default_factory=list, description="命中的关键词"
    )
    missing_keywords: list[str] = Field(
        default_factory=list, description="缺失的关键词"
    )
    comment: str = Field(..., description="评分说明")


class ResumeParseResponse(BaseModel):
    success: bool = True
    resume_id: Optional[str] = None
    resume: Optional[ResumeInfo] = None
    match: Optional[MatchResult] = None
    raw_text: Optional[str] = None
    error: Optional[str] = None


class MatchRequest(BaseModel):
    resume_id: str = Field(..., description="解析接口返回的简历 ID")
    job_description: str = Field(..., description="招聘岗位需求描述")


class MatchResponse(BaseModel):
    success: bool = True
    resume_id: str
    job_keywords: list[str] = Field(default_factory=list)
    job_summary: Optional[str] = None
    match: Optional[MatchResult] = None
    cached: bool = False
    error: Optional[str] = None


class JobKeywordResponse(BaseModel):
    success: bool = True
    keywords: list[str] = Field(default_factory=list)
    summary: Optional[str] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str = "ok"
    redis_available: bool = False
