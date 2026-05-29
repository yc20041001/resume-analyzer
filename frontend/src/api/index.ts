/** API client for the resume analyzer backend. */

const API_BASE = import.meta.env.VITE_API_BASE || "/api";

export interface Education {
  degree?: string;
  school?: string;
  major?: string;
  start_date?: string;
  end_date?: string;
}

export interface Project {
  name?: string;
  role?: string;
  description?: string;
  tech_stack?: string;
  highlights?: string;
}

export interface ResumeInfo {
  name?: string;
  phone?: string;
  email?: string;
  address?: string;
  job_intent?: string;
  expected_salary?: string;
  work_years?: string;
  education: Education[];
  projects: Project[];
}

export interface MatchResult {
  score: number;
  level: "excellent" | "good" | "fair" | "poor";
  skill_match_rate: number;
  experience_relevance: number;
  project_relevance: number;
  education_relevance: number;
  ai_score: number;
  matched_keywords: string[];
  missing_keywords: string[];
  comment: string;
}

export interface ResumeParseResponse {
  success: boolean;
  resume_id?: string;
  resume?: ResumeInfo;
  match?: MatchResult;
  job_keywords?: string[];
  job_summary?: string;
  raw_text?: string;
  error?: string;
}

export interface MatchResponse {
  success: boolean;
  resume_id: string;
  job_keywords: string[];
  job_summary?: string;
  match?: MatchResult;
  cached?: boolean;
  error?: string;
}

export interface JobKeywordResponse {
  success: boolean;
  keywords: string[];
  summary?: string;
  error?: string;
}

/** Upload a PDF resume and optionally match against a job description. */
export async function uploadResume(
  file: File,
  jobDescription?: string,
): Promise<ResumeParseResponse> {
  const form = new FormData();
  form.append("file", file);
  if (jobDescription) {
    form.append("job_description", jobDescription);
  }

  const res = await fetch(`${API_BASE}/resume/parse`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(detail.detail || `请求失败 (${res.status})`);
  }

  return res.json();
}

/** Match a parsed resume against a job description. */
export async function matchResume(
  resumeId: string,
  jobDescription: string,
): Promise<MatchResponse> {
  const res = await fetch(`${API_BASE}/resume/match`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      resume_id: resumeId,
      job_description: jobDescription,
    }),
  });

  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(detail.detail || `请求失败 (${res.status})`);
  }

  return res.json();
}

/** Extract keywords from a job description. */
export async function extractJobKeywords(
  jobDescription: string,
): Promise<JobKeywordResponse> {
  const form = new FormData();
  form.append("job_description", jobDescription);

  const res = await fetch(`${API_BASE}/job/keywords`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(detail.detail || `请求失败 (${res.status})`);
  }

  return res.json();
}
