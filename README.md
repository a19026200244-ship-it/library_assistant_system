# 智能图书馆助手系统

一个面向校园图书馆场景的智能问答助手，基于 `FastAPI`、`DeepSeek`、`LangChain`、`FAISS` 和原生 `HTML/CSS/JavaScript` 构建，支持图书查询、馆内规则问答、多轮对话记忆和语音交互。

## 项目简介

本项目将图书馆常见问答场景拆分为两类能力：

- 结构化检索：基于 `library_books.json` 查询图书名称、作者、分类、位置和借阅状态。
- 语义检索（RAG）：基于 `library_knowledge.txt` 构建向量知识库，回答开放时间、借阅规则、楼层分布等问题。

系统通过大模型的工具调用能力自动判断用户意图，并选择合适的检索方式生成自然语言回复。

## 功能特性

- 图书位置查询：支持按书名或作者模糊查询。
- 分类与状态查询：支持按分类、主题、在馆状态筛选图书。
- 图书推荐：根据兴趣关键词返回推荐书单。
- 图书馆规则问答：通过 RAG 回答馆内制度、开放时间、楼层信息等问题。
- 多轮对话记忆：保留最近若干轮会话上下文，支持“它”“那本书”等追问。
- Web 页面交互：提供原生 `HTML + CSS + JS` 聊天界面，方便演示与测试。
- 语音功能：支持浏览器语音识别和后端 TTS 音频合成播放。

## 技术栈

- 后端：`Python`、`FastAPI`、`Uvicorn`
- 大模型：`DeepSeek`（OpenAI 兼容接口）
- Agent：大模型 Function Calling
- RAG：`LangChain`、`HuggingFace Embeddings`、`FAISS`
- 前端：`HTML`、`CSS`、`JavaScript`
- 语音：浏览器 `SpeechRecognition`、`Edge-TTS`
- 数据：
  - `data/library_books.json`
  - `data/library_knowledge.txt`
  - `data/faiss_library_index/`

## 项目结构

```text
library_assistant_system/
├─ app.py                     # FastAPI 服务入口
├─ main.py                    # Agent 核心逻辑
├─ ingest.py                  # RAG 向量库构建脚本
├─ tts.py                     # 语音合成模块
├─ config.py                  # 项目配置
├─ index.html                 # Web 前端页面
├─ requirements.txt           # Python 依赖
├─ Dockerfile                 # Docker 构建文件
├─ docker-compose.yml         # Docker Compose 配置
├─ README_DEPLOY.md           # 部署说明
└─ data/
   ├─ library_books.json      # 图书结构化数据
   ├─ library_knowledge.txt   # 图书馆规则与知识文本
   └─ faiss_library_index/    # 向量检索索引
```

## 核心工作流程

### 1. 图书查询

用户提问后，Agent 会调用结构化查询工具，从 `library_books.json` 中检索相关图书信息，并返回位置、作者、分类和借阅状态。

### 2. RAG 规则问答

项目先通过 `ingest.py` 对 `library_knowledge.txt` 进行切片、向量化并构建 `FAISS` 索引。用户提问时，系统会从向量库中检索最相关的文本片段，再交给大模型组织自然语言答案。

### 3. 多轮对话记忆

系统会保留最近若干轮对话历史，并在每次请求时将历史消息与当前问题一起发送给模型，因此助手可以理解连续追问和代词指代。

## 本地运行

### 1. 克隆项目

```bash
git clone https://github.com/<your-username>/library_assistant_system.git
cd library_assistant_system
```

### 2. 创建虚拟环境

Windows PowerShell：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

macOS / Linux：

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

先复制示例文件：

Windows PowerShell：

```powershell
Copy-Item .env.example .env
```

macOS / Linux：

```bash
cp .env.example .env
```

然后在 `.env` 中填写你的 `DEEPSEEK_API_KEY`。

### 5. 检查 Embedding 设备

如果本机没有 GPU，请将 `config.py` 中的 `EMBEDDING_DEVICE` 修改为：

```python
EMBEDDING_DEVICE = "cpu"
```

### 6. 构建向量库

```bash
python ingest.py
```

运行后会生成：

```text
data/faiss_library_index/
```

### 7. 启动项目

```bash
python app.py
```

启动成功后访问：

```text
http://localhost:8000
```

## API 接口

### `GET /api/health`

检查服务是否正常启动。

### `POST /api/chat`

请求示例：

```json
{
  "message": "算法导论在哪？",
  "history": []
}
```

返回示例：

```json
{
  "answer": "《算法导论》在 3 楼 L3-C01 架。",
  "tool_results": [],
  "books": []
}
```

### `POST /api/tts`

请求示例：

```json
{
  "text": "欢迎来到智能图书馆。"
}
```

接口会返回可播放的 MP3 音频流。

## 示例问题

- `《算法导论》在哪？`
- `推荐几本计算机方面的书`
- `图书馆几点关门？`
- `借书可以续借吗？`
- `那它的作者是谁？`

## Docker 运行

### 1. 准备环境变量

```bash
cp .env.example .env
```

填写 `DEEPSEEK_API_KEY` 后执行：

```bash
docker-compose up -d --build
```

访问地址：

```text
http://localhost:8000
```

更多部署说明可查看 `README_DEPLOY.md`。

## 注意事项

- `data/faiss_library_index/` 为生成文件，可通过 `python ingest.py` 重新构建。
- 浏览器语音识别依赖 `SpeechRecognition`，推荐使用新版 Chrome 或 Edge。
- 如首次加载 Embedding 模型较慢，属于正常现象。
- 请勿将真实 API Key 提交到 GitHub。

## 后续可扩展方向

- 将书籍数据也纳入向量检索，实现更强的语义搜书。
- 增加用户登录与长期会话记忆。
- 增加借阅状态联动与数据库持久化。
- 将前端静态资源拆分为 `css` 和 `js` 文件，进一步规范工程结构。

## License

本项目仅用于学习、课程设计与技术演示。
