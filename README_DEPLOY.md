# 🚀 智能图书馆语音助手：部署与文件整理指南

本指南将帮助你规范化项目结构，并使用 Docker 进行云端部署。

---

## 📂 1. 项目文件规范化（已完成）

目前项目结构已调整为：

```text
library_assistant_system/
├── app.py             # FastAPI 入口 (后端服务)
├── index.html         # 前端展示 (HTML5/JS)
├── main.py            # Agent 核心逻辑 (DeepSeek & Tools)
├── tts.py             # TTS 语音合成模块 (Edge-TTS)
├── config.py          # 统一配置中心
├── ingest.py          # RAG 知识库构建脚本 (离线使用)
├── Dockerfile         # Docker 镜像配置文件 (新增)
├── docker-compose.yml # 容器编排配置文件 (新增)
├── requirements.txt   # 项目依赖
├── data/              # 📥 存放核心数据
│   ├── library_books.json     # 全量图书信息
│   ├── library_knowledge.txt  # RAG 语义知识原始文本
│   └── faiss_library_index/   # 核心向量库 (faiss)
└── .env               # 🔑 环境变量 (用户需自行创建)
```

**⚠️ 规范化注意点：**
- **数据解耦**: 所有静态数据和索引已存放在 `data/` 目录，通过 `config.py` 动态引用。
- **环境隔离**: 使用 `.env` 管理 API 密钥，不要将密钥硬编码到 `config.py` 或上传到 Git。
- **临时文件**: 代码中生成的语音文件在播放后会自动通过 `BackgroundTask` 安全删除，保持环境整洁。

---

## 🐳 2. Docker 部署方案

### A. 准备工作
在部署机器上确保已安装 `Docker` 和 `Docker Compose`。

### B. 常规步骤 (命令行)

1.  **克隆代码**: 将本项目上传至云服务器。
2.  **配置环境**: 基于 `.env.example` 复制一个 `.env` 文件。
    ```bash
    cp .env.example .env
    # 编辑 .env 文件，填写 DEEPSEEK_API_KEY
    ```
3.  **构建并启动镜像**:
    ```bash
    docker-compose up -d --build
    ```
4.  **访问**:
    默认监听 `8000` 端口，浏览器访问 `http://<服务器IP>:8000`。

---

## ☁️ 3. 云服务器常用部署流程

| 步骤 | 内容 |
| :--- | :--- |
| **步骤 1** | 分配云服务器 (推荐 Ubuntu 20.04/22.04) |
| **步骤 2** | 安装 Docker: `curl -fsSL https://get.docker.com \| sh` |
| **步骤 3** | 配置防火墙：开放 `8000` 端口入站规则 |
| **步骤 4** | 拉取代码并执行 `docker-compose up -d` |
| **步骤 5** | (可选) 使用 Nginx 进行反向代理并绑定域名 (支持 HTTPS) |

### 🛠️ RAG 库更新流程

如果你在本地修改了 `data/library_books.json` 或 `library_knowledge.txt`，需要运行 `python ingest.py` 重建索引，然后重新上传 `data/` 目录到云端，最后执行：
```bash
docker-compose restart
```

### 🔈 关于语音功能

Docker 容器中缺少音频输出硬件是正常的，但本系统在云端运行时：
1. `tts.py` 会在后台生成 MP3 文件。
2. 后端会通过 `FileResponse` 将文件传输至用户浏览器。
3. **播放行为完全发生在你（用户）的浏览器侧**，因此在云端 Docker 中完全可以使用高质量的 Edge-TTS。

---

🎉 祝你的智能图书馆系统部署顺利！
