"""LLM service — callable provider abstraction.

Supports any OpenAI-compatible API (OpenAI, DeepSeek, Qwen, etc.)
via environment variables: LLM_API_KEY, LLM_BASE_URL, LLM_MODEL.
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from openai import OpenAI
from app.config import settings

logger = logging.getLogger(__name__)

# Lazy-initialized client
_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    """Get or create the OpenAI client."""
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
        )
    return _client


def _system_prompt() -> str:
    return """你是一个专业的简历解析助手。请从简历文本中提取结构化信息，并以 JSON 格式返回。

请提取以下字段（如不存在则为 null）：
- name: 姓名
- phone: 电话号码
- email: 电子邮箱
- address: 地址
- job_intent: 求职意向 / 期望岗位
- expected_salary: 期望薪资
- work_years: 工作年限（数字 + "年"）
- education: 学历背景列表，每项包含 degree（学历）, school（学校）, major（专业）, start_date（开始时间）, end_date（结束时间）
- projects: 项目经历列表，每项包含 name（项目名称）, role（担任角色）, description（项目描述）, tech_stack（技术栈）, highlights（项目亮点）

请只输出 JSON，不要包含其他文字。"""


def extract_resume_info(resume_text: str) -> dict:
    """Use LLM to extract structured resume information."""
    prompt = f"请从以下简历文本中提取结构化信息：\n\n{resume_text}"
    return _call_llm([
        {"role": "system", "content": _system_prompt()},
        {"role": "user", "content": prompt},
    ])


def extract_job_keywords(job_description: str) -> tuple[list[str], str]:
    """Use LLM to extract keywords and summary from a job description."""
    prompt = (
        f"请从以下岗位描述中提取关键词并分析岗位要求。关键词应包含技术栈、工具框架、工作年限、学历、业务经验和软素质。"
        f"请以 JSON 格式返回，格式为："
        f'{{"keywords": ["关键词1", "关键词2", ...], "summary": "简短总结"}}\n\n'
        f"岗位描述：\n{job_description}"
    )
    result = _call_llm([
        {
            "role": "system",
            "content": "你是一个岗位分析助手。请提取关键词和总结，只输出 JSON。",
        },
        {"role": "user", "content": prompt},
    ])
    keywords = result.get("keywords", [])
    summary = result.get("summary", "")
    return keywords, summary


def match_resume_to_job(
    resume_text: str, resume_info: dict, job_description: str, job_keywords: list[str]
) -> dict:
    """Use LLM to score resume-job matching."""
    keywords_str = ", ".join(job_keywords) if job_keywords else "无"
    prompt = (
        f"请根据以下简历信息和岗位描述进行匹配评估。\n\n"
        f"简历文本（摘要）：\n{resume_text[:2000]}\n\n"
        f"简历结构化信息：\n{json.dumps(resume_info, ensure_ascii=False, indent=2)}\n\n"
        f"岗位描述：\n{job_description}\n\n"
        f"岗位关键词：{keywords_str}\n\n"
        f"请以 JSON 格式返回匹配结果：\n"
        f'{{"score": 0-100的整数, '
        f'"level": "excellent"|"good"|"fair"|"poor", '
        f'"skill_match_rate": 0到1的小数, '
        f'"experience_relevance": 0到1的小数, '
        f'"project_relevance": 0到1的小数, '
        f'"education_relevance": 0到1的小数, '
        f'"ai_score": 0到1的小数, '
        f'"matched_keywords": ["命中的关键词，只能是字符串，不要写解释"], '
        f'"missing_keywords": ["缺失的关键词，只能是字符串，不要写解释"], '
        f'"comment": "评分说明（中文）"}}'
    )
    return _call_llm([
        {
            "role": "system",
            "content": "你是一个专业的人才匹配助手。请客观评估简历与岗位的匹配度，只输出严格合法 JSON。数组元素必须是字符串，不能在数组内写括号解释或注释。",
        },
        {"role": "user", "content": prompt},
    ])


def _call_llm(messages: list[dict]) -> dict:
    """Call the LLM and parse the JSON response.

    Returns a dict on success, or an error dict on failure.
    """
    try:
        client = _get_client()
        resp = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=messages,
            temperature=0.1,
            max_tokens=2048,
        )
        content = resp.choices[0].message.content.strip()
        # Strip markdown code fences if present
        if content.startswith("```"):
            content = content.split("\n", 1)[-1]
            content = content.rsplit("```", 1)[0]
        return json.loads(content)
    except json.JSONDecodeError as exc:
        logger.error("LLM response JSON parse error: %s\nraw content: %s", exc, content)
        return {"error": f"AI 返回格式异常: {exc}", "_raw": content}
    except Exception as exc:
        logger.error("LLM call failed: %s", exc)
        return {"error": f"AI 服务调用失败: {exc}"}
