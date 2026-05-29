# AI 赋能的智能简历分析系统

> 一个支持 PDF 简历上传、AI 结构化提取、岗位需求匹配的智能分析系统。
> 笔试项目 — 24 小时内完成。

---

## 项目架构

```
resume-analyzer/
├── backend/                      # Python FastAPI 后端
│   ├── app/
│   │   ├── main.py              # FastAPI 应用入口
│   │   ├── config.py            # 环境变量配置
│   │   ├── cache.py             # Redis 缓存（可降级到内存）
│   │   ├── api/
│   │   │   └── routes.py        # API 路由定义
│   │   ├── models/
│   │   │   └── schemas.py       # Pydantic 请求/响应模型
│   │   └── services/
│   │       ├── pdf_parser.py    # PDF 文本提取（PyMuPDF + pdfplumber 双引擎）
│   │       ├── llm_service.py   # LLM 调用封装（OpenAI 兼容接口）
│   │       └── matcher.py       # 简历-岗位匹配编排
│   ├── requirements.txt
│   ├── Dockerfile               # Docker 部署
│   └── fc_bootstrap.py          # 阿里云函数计算入口
├── frontend/                     # React + Vite 前端
│   ├── src/
│   │   ├── App.tsx              # 主页面
│   │   ├── App.css              # 样式
│   │   ├── main.tsx             # 入口
│   │   ├── api/index.ts         # API 客户端
│   │   └── components/
│   │       ├── FileUpload.tsx   # PDF 上传组件
│   │       ├── JobDescription.tsx  # 岗位描述输入
│   │       ├── ParseResult.tsx  # 简历解析结果展示
│   │       └── ScoreResult.tsx  # 匹配评分展示
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── .env.example                  # 环境变量模板
└── README.md
```

## 技术选型

| 层 | 技术 | 说明 |
|---|---|---|
| 后端框架 | Python 3.11 + FastAPI | 高性能异步 Web 框架 |
| PDF 解析 | PyMuPDF + pdfplumber | 双引擎，自动切换 |
| AI 服务 | OpenAI 兼容 API | 支持 GPT / DeepSeek / 通义千问等，通过环境变量可切换 |
| 缓存 | Redis（可选） | 无 Redis 时自动降级为内存缓存 |
| 前端框架 | React 18 + TypeScript | Vite 构建 |
| 部署 | Docker / 阿里云 FC / GitHub Pages | 多平台支持 |

### 设计要点

- **LLM 服务抽象**：`llm_service.py` 封装了对 LLM 的调用，通过环境变量 `LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL` 可无缝切换不同厂商的模型，无需修改代码。
- **缓存降级**：`cache.py` 自动检测 Redis 是否可用，不可用则透明地使用 `dict` 做内存缓存，保证本地无 Redis 也能正常运行。
- **PDF 双引擎**：`pdf_parser.py` 优先使用 PyMuPDF（速度快），失败时自动切换到 pdfplumber，提高解析成功率。

---

## 本地运行方式

### 1. 后端

```bash
# 1. 克隆项目
cd resume-analyzer

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. 安装依赖
cd backend
pip install -r requirements.txt

# 4. 配置环境变量
cp ../.env.example .env
# 编辑 .env，填入 LLM_API_KEY

# 5. 启动服务
python -m app.main
# 服务启动在 http://localhost:8000
# API 文档：http://localhost:8000/docs
```

### 2. 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器（默认代理后端到 localhost:8000）
npm run dev
# 访问 http://localhost:5173
```

### 3. Docker 部署（后端）

```bash
cd backend
docker build -t resume-analyzer .
docker run -p 8000:8000 --env-file .env resume-analyzer
```

---

## 环境变量

| 变量 | 必填 | 默认值 | 说明 |
|---|---|---|---|
| `LLM_API_KEY` | 是 | — | API Key |
| `LLM_BASE_URL` | 否 | `https://api.openai.com/v1` | API 端点，可改为 DeepSeek/Qwen 等 |
| `LLM_MODEL` | 否 | `gpt-4o-mini` | 模型名称 |
| `REDIS_HOST` | 否 | — | Redis 地址，不填则使用内存缓存 |
| `REDIS_PORT` | 否 | `6379` | Redis 端口 |
| `REDIS_DB` | 否 | `0` | Redis 数据库编号 |
| `REDIS_TTL` | 否 | `3600` | 缓存过期时间（秒） |
| `HOST` | 否 | `0.0.0.0` | 监听地址 |
| `PORT` | 否 | `8000` | 监听端口 |
| `LOG_LEVEL` | 否 | `INFO` | 日志级别 |
| `FC_ENABLED` | 否 | `false` | 是否部署到阿里云 FC |

### 配置不同 LLM 示例

**DeepSeek：**
```bash
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
```

**阿里云通义千问（DashScope）：**
```bash
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus
```

---

## API 文档

### 健康检查

```
GET /api/health
```

响应：
```json
{
  "status": "ok",
  "redis_available": false
}
```

### 解析简历

```
POST /api/resume/parse
Content-Type: multipart/form-data

参数：
  file: File — PDF 简历文件（必填，仅支持 .pdf）
```

成功响应：
```json
{
  "success": true,
  "resume_id": "8f14e45fceea167a5a36dedd4bea2543",
  "resume": {
    "name": "张三",
    "phone": "13800138000",
    "email": "zhangsan@example.com",
    "address": "北京市朝阳区",
    "job_intent": "高级前端工程师",
    "expected_salary": "25K-35K",
    "work_years": "5年",
    "education": [
      { "degree": "本科", "school": "北京大学", "major": "计算机科学与技术",
        "start_date": "2015-09", "end_date": "2019-07" }
    ],
    "projects": [
      { "name": "电商平台重构", "role": "前端负责人",
        "description": "使用 React + TypeScript 重构...",
        "tech_stack": "React, TypeScript, Node.js",
        "highlights": "性能提升 40%" }
    ]
  },
  "raw_text": "张三 | 13800138000 | ..."
}
```

错误响应：
```json
{
  "success": false,
  "error": "无法从 PDF 中提取文本，请确认文件内容可复制"
}
```

### 简历与岗位匹配评分

```
POST /api/resume/match
Content-Type: application/json
```

请求：
```json
{
  "resume_id": "8f14e45fceea167a5a36dedd4bea2543",
  "job_description": "招聘 Java 后端开发工程师，熟悉 Spring Boot、MySQL、Redis，有 AI 大模型 API 调用经验优先。"
}
```

响应：
```json
{
  "success": true,
  "resume_id": "8f14e45fceea167a5a36dedd4bea2543",
  "job_keywords": ["Java", "Spring Boot", "MySQL", "Redis", "AI 大模型 API"],
  "job_summary": "岗位要求候选人具备 Java 后端开发、数据库、缓存和 AI API 接入能力。",
  "match": {
    "score": 86,
    "level": "good",
    "skill_match_rate": 0.82,
    "experience_relevance": 0.75,
    "project_relevance": 0.85,
    "education_relevance": 0.8,
    "ai_score": 0.86,
    "matched_keywords": ["Java", "Spring Boot", "MySQL", "Redis"],
    "missing_keywords": ["Docker"],
    "comment": "候选人后端技术栈与岗位较匹配，具备相关项目经验，但 Docker 经验体现较少。"
  },
  "cached": false,
  "error": null
}
```

### 提取岗位关键词

```
POST /api/job/keywords
Content-Type: multipart/form-data

参数：
  job_description: str — 岗位描述文本（必填）
```

响应：
```json
{
  "success": true,
  "keywords": ["React", "TypeScript", "Node.js", "微服务"],
  "summary": "招聘高级前端工程师，要求...",
  "error": null
}
```

---

## 阿里云函数计算部署说明

### 方式一：使用 Custom Runtime 部署（推荐）

1. **构建镜像**：
   ```bash
   cd backend
   docker build -t resume-analyzer-fc .
   ```

2. **推送到阿里云容器镜像服务**：
   ```bash
   docker tag resume-analyzer-fc registry.cn-hangzhou.aliyuncs.com/your-ns/resume-analyzer:latest
   docker push registry.cn-hangzhou.aliyuncs.com/your-ns/resume-analyzer:latest
   ```

3. **创建函数**：
   - 进入 FC 控制台 → 创建函数 → **使用容器镜像**
   - 选择推送的镜像
   - 设置启动命令：`uvicorn app.main:app --host 0.0.0.0 --port 9000`
   - 设置监听端口：`9000`
   - 配置环境变量（在 FC 控制台设置）：
     - `LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL`
     - 如果使用 Redis：`REDIS_HOST`、`REDIS_PORT`、`REDIS_DB`

4. **配置触发器**：
   - 创建 HTTP 触发器，设置允许的方法：`GET`、`POST`、`OPTIONS`
   - 认证方式：`无需认证`（或根据需要选择）

5. **注意事项**：
   - 函数计算的请求/响应体大小限制为 6 MB，超大 PDF 建议先上传到 OSS
   - LLM 调用可能超时，建议将 FC 超时时间设为 120 秒以上
   - 如需更精细的文件处理，可使用 FC 的 `oss` 事件触发 + 异步处理

### 方式二：使用 Python Runtime + fc_bootstrap.py

直接部署 `fc_bootstrap.py` 作为入口，通过 `handler` 函数处理请求。

---

## 前端部署说明

### GitHub Pages

1. **修改 vite.config.ts**，设置正确的 `base`：
   ```ts
   base: "/your-repo-name/",  // GitHub 仓库名
   ```

2. **构建**：
   ```bash
   cd frontend
   npm run build
   ```

3. **部署**：
   - 方式一：将 `dist/` 目录推送到 `gh-pages` 分支
   - 方式二：使用 GitHub Actions

   GitHub Actions 示例（`.github/workflows/deploy.yml`）：
   ```yaml
   name: Deploy to GitHub Pages
   on:
     push:
       branches: [main]
   jobs:
     deploy:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-node@v4
           with:
             node-version: 20
         - run: cd frontend && npm ci && npm run build
         - uses: peaceiris/actions-gh-pages@v3
           with:
             github_token: ${{ secrets.GITHUB_TOKEN }}
             publish_dir: ./frontend/dist
   ```

4. **配置 API 地址**：
   在前端仓库的 Settings → Pages 下设置环境变量 `VITE_API_BASE` 指向后端部署地址：
   ```
   VITE_API_BASE=https://your-fc-url.com/api
   ```

### 注意事项

- GitHub Pages 是静态托管，需要单独部署后端服务
- 开发时 Vite 的代理配置已处理好跨域，生产环境需要在后端配置 CORS
- 后端已配置了 CORS 中间件，支持 `*.github.io`

---

## 常见问题

**Q: 本地没有 Redis 能运行吗？**
A: 可以。不设置 `REDIS_HOST` 即可，系统会自动使用内存缓存。

**Q: 支持哪些 PDF 格式？**
A: 支持标准文本型 PDF。扫描件（图片型 PDF）需要先 OCR，本系统暂不内置 OCR 功能。

**Q: 不想用 OpenAI，能用其他模型吗？**
A: 可以。修改 `LLM_BASE_URL` 和 `LLM_MODEL` 即可切换任意兼容 OpenAI 接口的服务（如 DeepSeek、通义千问、Claude 等）。

**Q: 最大支持多大的 PDF？**
A: 10 MB。可通过环境变量 `MAX_FILE_SIZE` 调整（单位字节）。

---

## License

MIT
