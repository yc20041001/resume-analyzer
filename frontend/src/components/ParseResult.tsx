import type { ResumeInfo } from "../api";

interface Props {
  resume: ResumeInfo;
}

function Field({ label, value }: { label: string; value?: string | null }) {
  if (!value) return null;
  return (
    <div className="field">
      <span className="field-label">{label}</span>
      <span className="field-value">{value}</span>
    </div>
  );
}

export default function ParseResult({ resume }: Props) {
  return (
    <div className="card">
      <h3>简历解析结果</h3>

      <div className="resume-section">
        <h4>基本信息</h4>
        <Field label="姓名" value={resume.name} />
        <Field label="电话" value={resume.phone} />
        <Field label="邮箱" value={resume.email} />
        <Field label="地址" value={resume.address} />
        <Field label="求职意向" value={resume.job_intent} />
        <Field label="期望薪资" value={resume.expected_salary} />
        <Field label="工作年限" value={resume.work_years} />
      </div>

      {resume.education.length > 0 && (
        <div className="resume-section">
          <h4>学历背景</h4>
          {resume.education.map((edu, i) => (
            <div key={i} className="sub-item">
              <div><strong>{edu.school || "—"}</strong> {edu.degree || ""}</div>
              <div>{edu.major || ""} {edu.start_date && `${edu.start_date} ~ ${edu.end_date || ""}`}</div>
            </div>
          ))}
        </div>
      )}

      {resume.projects.length > 0 && (
        <div className="resume-section">
          <h4>项目经历</h4>
          {resume.projects.map((proj, i) => (
            <div key={i} className="sub-item">
              <div><strong>{proj.name || "—"}</strong> {proj.role ? `(${proj.role})` : ""}</div>
              {proj.description && <p>{proj.description}</p>}
              {proj.tech_stack && <div className="tech-stack">技术栈：{proj.tech_stack}</div>}
              {proj.highlights && <div className="highlight">{proj.highlights}</div>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
