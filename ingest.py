"""
ingest.py - RAG 向量库构建脚本

功能：读取知识库文本 → 切片 → 向量化 → 保存为 FAISS 索引
用法：python ingest.py
"""

import logging

from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

import config

# --- 日志配置 ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def create_vector_db():
    """构建 FAISS 向量索引并保存到本地"""

    # 1. 加载文档
    logger.info(f"正在读取知识库: {config.KNOWLEDGE_TXT_PATH}")
    try:
        with open(config.KNOWLEDGE_TXT_PATH, "r", encoding="utf-8") as f:
            raw_text = f.read()
    except FileNotFoundError:
        logger.error(f"文件不存在: {config.KNOWLEDGE_TXT_PATH}")
        logger.error("请先创建 library_knowledge.txt 文件")
        return
    except UnicodeDecodeError:
        logger.error("文件编码错误，请确保文件为 UTF-8 编码")
        return

    if not raw_text.strip():
        logger.error("知识库文件为空，请先填写内容")
        return

    # 2. 文本切片
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
    )
    texts = text_splitter.split_text(raw_text)
    logger.info(f"文档切分为 {len(texts)} 个片段 (chunk_size={config.CHUNK_SIZE})")

    # 3. 加载 Embedding 模型
    logger.info(f"正在加载 Embedding 模型: {config.EMBEDDING_MODEL_NAME}")
    logger.info("首次运行需下载模型，请保持网络畅通...")
    try:
        embeddings = HuggingFaceEmbeddings(
            model_name=config.EMBEDDING_MODEL_NAME,
            model_kwargs={"device": config.EMBEDDING_DEVICE},
            encode_kwargs={"normalize_embeddings": True},
        )
    except Exception as e:
        logger.error(f"Embedding 模型加载失败: {e}")
        logger.error("如果没有 GPU，请在 config.py 中将 EMBEDDING_DEVICE 改为 'cpu'")
        return

    # 4. 构建并保存 FAISS 索引
    logger.info("正在构建向量索引...")
    try:
        import os
        # 确保目录存在
        if not os.path.exists(config.FAISS_INDEX_PATH):
            os.makedirs(config.FAISS_INDEX_PATH)
            logger.info(f"创建了目录: {config.FAISS_INDEX_PATH}")
            
        vector_db = FAISS.from_texts(texts, embeddings)
        vector_db.save_local(config.FAISS_INDEX_PATH)
        logger.info(f"向量库构建完成！已保存至: {config.FAISS_INDEX_PATH}")
    except Exception as e:
        logger.error(f"向量库构建失败，详细错误: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return


if __name__ == "__main__":
    create_vector_db()
