# 智能图书馆助手系统

一个面向校园图书馆场景的智能问答与语音交互系统，基于 `FastAPI`、`DeepSeek`、`LangChain` 和 `FAISS` 构建，支持图书检索、馆内规则问答、多轮对话记忆、语音交互与 Web 演示。

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![DeepSeek](https://img.shields.io/badge/DeepSeek-LLM-4D6BFE)](https://www.deepseek.com/)
[![LangChain](https://img.shields.io/badge/LangChain-RAG-1C3C3C?logo=langchain&logoColor=white)](https://www.langchain.com/)
[![FAISS](https://img.shields.io/badge/FAISS-Vector_Search-0467DF)](https://github.com/facebookresearch/faiss)
[![Frontend](https://img.shields.io/badge/Frontend-HTML%20%2B%20CSS%20%2B%20JS-E34F26?logo=html5&logoColor=white)](https://developer.mozilla.org/)
[![Status](https://img.shields.io/badge/Status-Demo-success)]()

## 项目亮点

- 支持图书位置、作者、分类和借阅状态查询
- 支持开放时间、借阅规则、楼层分布等馆内知识问答
- 集成 `RAG + FAISS` 语义检索，提高问答准确率
- 支持多轮对话记忆，可理解“它”“那本书”等连续追问
- 支持浏览器语音输入与后端 TTS 语音播报
- 提供原生 `HTML + CSS + JavaScript` Web 界面，方便演示和测试

## 项目简介

本项目将图书馆问答场景拆分为两类能力：

- 结构化检索：基于 `data/library_books.json` 查询图书名称、作者、分类、位置和借阅状态
- 语义检索（RAG）：基于 `data/library_knowledge.txt` 构建向量知识库，回答开放时间、借阅规则、楼层信息等问题

系统通过大模型的工具调用能力自动判断用户意图，并选择合适的检索方式生成自然语言回复。

## 技术栈

- 后端：`Python`、`FastAPI`、`Uvicorn`
- 大模型：`DeepSeek`（OpenAI 兼容接口）
- Agent：Function Calling
- RAG：`LangChain`、`HuggingFace Embeddings`、`FAISS`
- 前端：`HTML`、`CSS`、`JavaScript`
- 语音：浏览器 `SpeechRecognition`、`Edge-TTS`
- 数据源：
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

## 核心能力

### 1. 图书查询

系统支持按书名、作者、分类和状态进行结构化检索，适合处理：

- `《算法导论》在哪？`
- `推荐几本计算机方面的书`
- `哪些书已经被借出了？`

### 2. RAG 规则问答

项目通过 `ingest.py` 对 `library_knowledge.txt` 进行切片、向量化并构建 `FAISS` 索引。用户提问时，系统先从向量库中检索最相关的文本片段，再交给大模型组织自然语言答案。

适合处理：

- `图书馆几点关门？`
- `借书可以续借吗？`
- `3 楼有什么？`

### 3. 多轮对话记忆

系统会保留最近若干轮对话历史，并在每次请求时将历史消息与当前问题一同发送给模型，因此助手可以理解连续追问和代词指代。

示例：

```text
用户：算法导论在哪？
助手：在 3 楼 L3-C01 架。
用户：那它的作者是谁？
助手：它的作者是科曼。
```

## 快速开始

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

Windows PowerShell：

```powershell
Copy-Item .env.example .env
```

macOS / Linux：

```bash
cp .env.example .env
```

然后在 `.env` 中填写：

```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

### 5. 配置 Embedding 设备

如果本机没有 GPU，请在 `config.py` 中设置：

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

浏览器访问：

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

更多部署细节可查看 `README_DEPLOY.md`。

## 注意事项

- `data/faiss_library_index/` 为生成文件，可通过 `python ingest.py` 重新构建
- 浏览器语音识别依赖 `SpeechRecognition`，推荐使用新版 Chrome 或 Edge
- 首次加载 Embedding 模型较慢属于正常现象
- 请勿将真实 API Key 提交到 GitHub

## 后续可扩展方向

- 将书籍数据也纳入向量检索，实现更强的语义搜书
- 增加用户登录与长期会话记忆
- 增加借阅状态联动与数据库持久化
- 将前端静态资源拆分为独立 `css` 和 `js` 文件，进一步规范工程结构

## License

本项目仅用于学习、课程设计与技术演示。
