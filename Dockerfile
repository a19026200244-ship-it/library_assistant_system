# 使用官方轻量级 Python 镜像
FROM python:3.11-slim

# 设置容器内的环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 工作目录
WORKDIR /app

# 安装系统级依赖 (ffmpeg 用于音频处理)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装 Python 库
# 我们可以在安装前删除不需要在容器中运行的依赖（如 pygame 和 gradio）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目源代码和数据
COPY . .

# 暴露 FastAPI 运行的端口
EXPOSE 8000

# 启动命令
# 使用 uvicorn 运行主应用
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
