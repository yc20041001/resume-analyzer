import type { MatchResult } from "../api";

interface Props {
  match: MatchResult;
}

const LEVEL_LABEL: Record<string, string> = {
  excellent: "高度匹配",
  good: "比较匹配",
  fair: "一般匹配",
  poor: "不太匹配",
};

const LEVEL_COLOR: Record<string, string> = {
  excellent: "#22c55e",
  good: "#3b82f6",
  fair: "#eab308",
  poor: "#ef4444",
};

function getScoreColor(score: number): string {
  if (score >= 80) return LEVEL_COLOR.excellent;
  if (score >= 60) return LEVEL_COLOR.good;
  if (score >= 40) return LEVEL_COLOR.fair;
  return LEVEL_COLOR.poor;
}

export default function ScoreResult({ match }: Props) {
  const color = getScoreColor(match.score);
  const details = [
    ["技能匹配率", match.skill_match_rate],
    ["工作经验相关性", match.experience_relevance],
    ["项目经历相关性", match.project_relevance],
    ["学历背景匹配度", match.education_relevance],
    ["AI 综合评分", match.ai_score],
  ];

  return (
    <div className="card">
      <h3>匹配评分</h3>

      <div className="score-header">
        <div className="score-ring" style={{ borderColor: color }}>
          <span className="score-number" style={{ color }}>{match.score}</span>
          <span className="score-unit">/100</span>
        </div>
        <div className="score-level" style={{ color }}>
          {LEVEL_LABEL[match.level] || match.level}
        </div>
      </div>

      <div className="score-detail-grid">
        {details.map(([label, value]) => (
          <div key={label as string} className="score-detail-item">
            <span>{label}</span>
            <strong>{Math.round((value as number) * 100)}%</strong>
          </div>
        ))}
      </div>

      <div className="keyword-section">
        <div className="keyword-group">
          <h4>命中关键词 ({match.matched_keywords.length})</h4>
          <div className="keyword-tags">
            {match.matched_keywords.map((kw, i) => (
              <span key={i} className="tag tag-hit">{kw}</span>
            ))}
            {match.matched_keywords.length === 0 && (
              <span className="empty-hint">无</span>
            )}
          </div>
        </div>

        <div className="keyword-group">
          <h4>缺失关键词 ({match.missing_keywords.length})</h4>
          <div className="keyword-tags">
            {match.missing_keywords.map((kw, i) => (
              <span key={i} className="tag tag-miss">{kw}</span>
            ))}
            {match.missing_keywords.length === 0 && (
              <span className="empty-hint">无</span>
            )}
          </div>
        </div>
      </div>

      <div className="comment-box">
        <h4>评分说明</h4>
        <p>{match.comment}</p>
      </div>
    </div>
  );
}
