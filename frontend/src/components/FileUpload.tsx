import { useRef, useState } from "react";

interface Props {
  onFileSelected: (file: File) => void;
}

export default function FileUpload({ onFileSelected }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [fileName, setFileName] = useState<string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      alert("仅支持 PDF 格式文件");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      alert("文件大小超过限制（最大 10 MB）");
      return;
    }
    setFileName(file.name);
    onFileSelected(file);
  };

  return (
    <div className="card">
      <h3>上传简历 (PDF)</h3>
      <div className="upload-area">
        <input
          ref={inputRef}
          type="file"
          accept=".pdf"
          onChange={handleChange}
          hidden
        />
        <button onClick={() => inputRef.current?.click()}>
          {fileName ? "重新选择" : "选择 PDF 文件"}
        </button>
        {fileName && <span className="file-name">{fileName}</span>}
      </div>
    </div>
  );
}
