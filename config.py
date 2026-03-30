"""
config.py - 统一配置管理

所有可配置项集中在此，避免散落在各文件中
"""

import os

# --- 路径配置 ---
# 项目根目录（以 config.py 所在目录为基准，保证任何地方运行都能找到文件）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

# 数据文件路径
DATA_DIR = os.path.join(BASE_DIR, "data")
BOOKS_JSON_PATH = os.path.join(DATA_DIR, "library_books.json")
KNOWLEDGE_TXT_PATH = os.path.join(DATA_DIR, "library_knowledge.txt")
FAISS_INDEX_PATH = os.path.join(DATA_DIR, "faiss_library_index")

# --- LLM 配置 ---
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"

# --- Embedding 模型配置 ---
EMBEDDING_MODEL_NAME = "BAAI/bge-small-zh-v1.5"
EMBEDDING_DEVICE = "cuda"  # 没有 GPU 改为 "cpu"

# --- RAG 配置 ---
CHUNK_SIZE = 400        # 文本切片大小
CHUNK_OVERLAP = 50      # 切片重叠长度
SIMILARITY_TOP_K = 3    # 相似度检索返回的文档数量

# --- TTS 配置 ---
TTS_VOICE = "zh-CN-XiaoxiaoNeural"  # 微软晓晓，中文女声
TTS_OUTPUT_FILE = os.path.join(BASE_DIR, "tts_output.mp3")

# --- Agent 配置 ---
SYSTEM_PROMPT = (
    "你是一个智能图书馆语音助手，名叫'小星'，属于桂林电子科技大学图书馆。"
    "你可以查询图书位置、馆内规章制度、推荐书籍等。\n\n"
    "## 回答格式要求：\n"
    "1. 用亲切、口语化的语言回答，像朋友一样自然\n"
    "2. 使用 Markdown 格式让回答更有条理：\n"
    "   - 使用 **加粗** 标注重要信息（书名、位置、时间等）\n"
    "   - 多条信息时使用编号列表（1. 2. 3.）\n"
    "   - 子项使用无序列表（-）\n"
    "3. 推荐书籍时按分类用编号列出，每个分类下用 - 列出具体书名\n"
    "4. 回答简洁有用，不要过度使用emoji\n"
    "5. 结合对话历史进行连贯的对话\n"
)

# --- 对话记忆配置 ---
MAX_HISTORY_ROUNDS = 10  # 保留最近 N 轮对话（1轮 = 用户问 + 助手答）
