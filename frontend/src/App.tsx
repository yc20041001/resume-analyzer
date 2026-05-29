import { useState } from "react";
import FileUpload from "./components/FileUpload";
import JobDescription from "./components/JobDescription";
import ParseResult from "./components/ParseResult";
import ScoreResult from "./components/ScoreResult";
import { matchResume, uploadResume, type ResumeParseResponse } from "./api";
import "./App.css";

export default function App() {
  const [file, setFile] = useState<File | null>(null);
  const [jd, setJd] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ResumeParseResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!file) {
      alert("请先选择一份 PDF 简历");
      return;
    }
    if (!jd.trim()) {
      alert("请填写岗位描述，系统需要根据岗位需求计算匹配评分");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await uploadResume(file);
      if (!data.success) {
        setError(data.error || "解析失败");
      } else {
        let nextResult = data;
        if (data.resume_id) {
          const matchData = await matchResume(data.resume_id, jd.trim());
          if (!matchData.success) {
            setError(matchData.error || "匹配评分失败");
          }
          nextResult = {
            ...data,
            match: matchData.match,
            job_keywords: matchData.job_keywords,
            job_summary: matchData.job_summary,
          };
        }
        setResult(nextResult);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "网络请求失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>AI 简历分析系统</h1>
        <p className="subtitle">上传 PDF 简历，提取结构化信息，匹配岗位需求</p>
      </header>

      <main className="app-main">
        <div className="input-section">
          <FileUpload onFileSelected={(f) => setFile(f)} />
          <JobDescription value={jd} onChange={setJd} disabled={loading} />
          <button
            className="submit-btn"
            onClick={handleSubmit}
            disabled={loading || !file || !jd.trim()}
          >
            {loading ? "分析评分中…" : "开始解析并评分"}
          </button>
        </div>

        {error && (
          <div className="error-box">
            <strong>错误：</strong> {error}
          </div>
        )}

        {result && (
          <div className="result-section">
            {result.resume && <ParseResult resume={result.resume} />}
            {result.job_keywords && result.job_keywords.length > 0 && (
              <div className="card">
                <h3>岗位关键词分析</h3>
                {result.job_summary && (
                  <p className="job-summary">{result.job_summary}</p>
                )}
                <div className="keyword-tags">
                  {result.job_keywords.map((kw, i) => (
                    <span key={i} className="tag tag-job">{kw}</span>
                  ))}
                </div>
              </div>
            )}
            {result.match && <ScoreResult match={result.match} />}
            {result.raw_text && (
              <details className="card raw-text-card">
                <summary>查看原始文本片段</summary>
                <pre>{result.raw_text}</pre>
              </details>
            )}
          </div>
        )}
      </main>

      <footer className="app-footer">
        <p>AI Resume Analyzer &mdash; 笔试项目</p>
      </footer>
    </div>
  );
}
