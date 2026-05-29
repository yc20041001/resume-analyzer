"""Resume-job matching orchestrator."""

from __future__ import annotations

import logging
import re
from typing import Optional

from app.cache import cache
from app.models.schemas import (
    Education,
    MatchLevel,
    MatchResult,
    Project,
    ResumeInfo,
)
from app.services.llm_service import (
    extract_job_keywords,
    extract_resume_info,
    match_resume_to_job,
)

logger = logging.getLogger(__name__)


def _as_text(value) -> Optional[str]:
    """Normalize loose LLM output into an optional string."""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "，".join(str(item) for item in value if item is not None)
    return str(value)


def _as_string_list(value) -> list[str]:
    """Normalize loose LLM output into a list of strings."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if item is not None]
    if isinstance(value, str):
        return [value] if value else []
    return [str(value)]


def _as_score(value) -> int:
    """Normalize LLM score output into a 0-100 integer."""
    if isinstance(value, (int, float)):
        return max(0, min(100, int(value)))
    if isinstance(value, str):
        match = re.search(r"\d+", value)
        if match:
            return max(0, min(100, int(match.group())))
    return 0


def _as_ratio(value) -> float:
    """Normalize LLM ratio output into a 0-1 float."""
    if isinstance(value, (int, float)):
        ratio = float(value)
        return max(0, min(1, ratio / 100 if ratio > 1 else ratio))
    if isinstance(value, str):
        match = re.search(r"\d+(?:\.\d+)?", value)
        if match:
            ratio = float(match.group())
            return max(0, min(1, ratio / 100 if ratio > 1 else ratio))
    return 0


def _contains_any(text: str, words: list[str]) -> bool:
    return any(word and word.lower() in text.lower() for word in words)


def _rule_based_detail(
    resume_text: str,
    resume_info: ResumeInfo,
    job_keywords: list[str],
) -> dict[str, float | list[str]]:
    """Calculate explainable baseline matching metrics."""
    normalized_keywords = [kw for kw in _as_string_list(job_keywords) if kw.strip()]
    resume_blob = " ".join(
        [
            resume_text,
            resume_info.job_intent or "",
            resume_info.work_years or "",
            " ".join(
                " ".join(
                    [
                        project.name or "",
                        project.role or "",
                        project.description or "",
                        project.tech_stack or "",
                        project.highlights or "",
                    ]
                )
                for project in resume_info.projects
            ),
            " ".join(
                " ".join(
                    [
                        education.degree or "",
                        education.school or "",
                        education.major or "",
                    ]
                )
                for education in resume_info.education
            ),
        ]
    )
    matched = [kw for kw in normalized_keywords if kw.lower() in resume_blob.lower()]
    missing = [kw for kw in normalized_keywords if kw not in matched]
    skill_match_rate = len(matched) / len(normalized_keywords) if normalized_keywords else 0

    experience_words = ["年", "经验", "实习", "工作", "开发", "负责", "参与"]
    project_words = ["项目", "系统", "平台", "服务", "模块", "接口", "部署"]
    education_words = ["本科", "专科", "硕士", "博士", "大学", "学院", "专业"]

    experience_relevance = 0.75 if _contains_any(resume_blob, experience_words) else 0.25
    project_relevance = 0.85 if resume_info.projects else (0.5 if _contains_any(resume_blob, project_words) else 0.2)
    education_relevance = 0.8 if resume_info.education else (0.45 if _contains_any(resume_blob, education_words) else 0.2)

    return {
        "skill_match_rate": round(skill_match_rate, 2),
        "experience_relevance": round(experience_relevance, 2),
        "project_relevance": round(project_relevance, 2),
        "education_relevance": round(education_relevance, 2),
        "ai_score": 0.65,
        "matched_keywords": matched,
        "missing_keywords": missing,
    }


def _build_rule_based_match(fallback: dict) -> MatchResult:
    """Build a deterministic match result when the LLM response is invalid."""
    skill_match_rate = _as_ratio(fallback.get("skill_match_rate"))
    experience_relevance = _as_ratio(fallback.get("experience_relevance"))
    project_relevance = _as_ratio(fallback.get("project_relevance"))
    education_relevance = _as_ratio(fallback.get("education_relevance"))
    ai_score = _as_ratio(fallback.get("ai_score"))
    score = round(
        (
            skill_match_rate * 0.4
            + experience_relevance * 0.25
            + project_relevance * 0.2
            + education_relevance * 0.1
            + ai_score * 0.05
        )
        * 100
    )
    if score >= 85:
        level = MatchLevel.excellent
    elif score >= 65:
        level = MatchLevel.good
    elif score >= 45:
        level = MatchLevel.fair
    else:
        level = MatchLevel.poor

    return MatchResult(
        score=score,
        level=level,
        skill_match_rate=skill_match_rate,
        experience_relevance=experience_relevance,
        project_relevance=project_relevance,
        education_relevance=education_relevance,
        ai_score=ai_score,
        matched_keywords=_as_string_list(fallback.get("matched_keywords")),
        missing_keywords=_as_string_list(fallback.get("missing_keywords")),
        comment="AI 返回格式异常，系统已使用规则评分兜底：根据岗位关键词命中、工作经验、项目经历和学历背景计算匹配度。",
    )


def _build_resume_info(data: dict) -> ResumeInfo:
    """Map raw LLM response dict to ResumeInfo."""
    if "error" in data:
        raise ValueError(data["error"])

    educations = []
    for item in data.get("education") or []:
        if isinstance(item, dict):
            educations.append(
                Education(
                    degree=_as_text(item.get("degree")),
                    school=_as_text(item.get("school")),
                    major=_as_text(item.get("major")),
                    start_date=_as_text(item.get("start_date")),
                    end_date=_as_text(item.get("end_date")),
                )
            )

    projects = []
    for item in data.get("projects") or []:
        if isinstance(item, dict):
            projects.append(
                Project(
                    name=_as_text(item.get("name")),
                    role=_as_text(item.get("role")),
                    description=_as_text(item.get("description")),
                    tech_stack=_as_text(item.get("tech_stack")),
                    highlights=_as_text(item.get("highlights")),
                )
            )

    return ResumeInfo(
        name=_as_text(data.get("name")),
        phone=_as_text(data.get("phone")),
        email=_as_text(data.get("email")),
        address=_as_text(data.get("address")),
        job_intent=_as_text(data.get("job_intent")),
        expected_salary=_as_text(data.get("expected_salary")),
        work_years=_as_text(data.get("work_years")),
        education=educations,
        projects=projects,
    )


def _build_match_result(data: dict, fallback: Optional[dict] = None) -> MatchResult:
    """Map raw LLM response dict to MatchResult."""
    if "error" in data:
        raise ValueError(data["error"])
    fallback = fallback or {}

    level_raw = data.get("level", "fair")
    try:
        level = MatchLevel(level_raw)
    except ValueError:
        level = MatchLevel.fair

    score = _as_score(data.get("score"))
    skill_match_rate = _as_ratio(
        data.get("skill_match_rate", fallback.get("skill_match_rate", 0))
    )
    experience_relevance = _as_ratio(
        data.get("experience_relevance", fallback.get("experience_relevance", 0))
    )
    project_relevance = _as_ratio(
        data.get("project_relevance", fallback.get("project_relevance", 0))
    )
    education_relevance = _as_ratio(
        data.get("education_relevance", fallback.get("education_relevance", 0))
    )
    ai_score = _as_ratio(data.get("ai_score", score / 100 if score else 0))

    if not score:
        score = round(
            (
                skill_match_rate * 0.4
                + experience_relevance * 0.25
                + project_relevance * 0.2
                + education_relevance * 0.1
                + ai_score * 0.05
            )
            * 100
        )

    return MatchResult(
        score=score,
        level=level,
        skill_match_rate=skill_match_rate,
        experience_relevance=experience_relevance,
        project_relevance=project_relevance,
        education_relevance=education_relevance,
        ai_score=ai_score,
        matched_keywords=_as_string_list(
            data.get("matched_keywords", fallback.get("matched_keywords"))
        ),
        missing_keywords=_as_string_list(
            data.get("missing_keywords", fallback.get("missing_keywords"))
        ),
        comment=_as_text(data.get("comment")) or "",
    )


async def parse_resume(resume_text: str) -> Optional[ResumeInfo]:
    """Parse resume text into structured ResumeInfo."""
    cached = await cache.get("resume", resume_text)
    if cached:
        return ResumeInfo(**cached) if cached.get("name") else None

    data = extract_resume_info(resume_text)
    if "error" in data:
        logger.error("Resume parsing failed: %s", data["error"])
        return None

    try:
        info = _build_resume_info(data)
    except Exception as exc:
        logger.exception("Resume response normalization failed: %s", exc)
        return None
    await cache.set("resume", resume_text, info.model_dump())
    return info


async def extract_keywords(
    job_description: str,
) -> tuple[list[str], str]:
    """Extract keywords and summary from job description."""
    cached = await cache.get("keywords", job_description)
    if cached:
        return cached.get("keywords", []), cached.get("summary", "")

    keywords, summary = extract_job_keywords(job_description)
    await cache.set("keywords", job_description, {"keywords": keywords, "summary": summary})
    return keywords, summary


async def compute_match(
    resume_text: str,
    resume_info: ResumeInfo,
    job_description: str,
    job_keywords: list[str],
) -> Optional[MatchResult]:
    """Compute matching score between resume and job description."""
    cache_key = f"{resume_text[:500]}|{job_description[:500]}"
    cached = await cache.get("match", cache_key)
    if cached:
        return _build_match_result(cached)

    fallback = _rule_based_detail(resume_text, resume_info, job_keywords)
    data = match_resume_to_job(
        resume_text,
        resume_info.model_dump(),
        job_description,
        job_keywords,
    )
    if "error" in data:
        logger.error("Matching failed: %s", data["error"])
        result = _build_rule_based_match(fallback)
        await cache.set("match", cache_key, result.model_dump())
        return result

    try:
        result = _build_match_result(data, fallback)
    except Exception as exc:
        logger.exception("Match response normalization failed: %s", exc)
        return None
    await cache.set("match", cache_key, result.model_dump())
    return result
