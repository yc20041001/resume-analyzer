interface Props {
  value: string;
  onChange: (v: string) => void;
  disabled?: boolean;
}

export default function JobDescription({ value, onChange, disabled }: Props) {
  return (
    <div className="card">
      <h3>岗位描述（必填，用于匹配评分）</h3>
      <textarea
        rows={6}
        placeholder="粘贴岗位描述 / JD 文本，例如：招聘 Java 后端开发工程师，要求熟悉 Spring Boot、MySQL、Redis，有 AI 大模型 API 接入经验优先…"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
      />
    </div>
  );
}
