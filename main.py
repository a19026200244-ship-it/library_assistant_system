"""
main.py - 智能图书馆语音助手 (Agent 核心程序)

功能：基于 DeepSeek + RAG + Agent 的智能问答系统
工具：查询图书位置、检索馆内规章制度
"""

import json
import logging
from typing import Any

import config
from openai import OpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

from tts import speak

# --- 日志配置 ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ============================================================
#  1. 初始化：统一封装，带异常保护
# ============================================================

# --- 全局组件 (在初始化后赋值) ---
client = None
vector_db = None
books_data = None


def initialize_system(force: bool = False) -> None:
    """初始化所有全局组件，供 CLI 和 Web 前端复用。"""
    global client, vector_db, books_data

    if force or client is None:
        client = init_llm_client()
    if force or vector_db is None:
        vector_db = init_vector_db()
    if force or books_data is None:
        books_data = init_books_data()


def init_llm_client() -> OpenAI:
    """初始化 DeepSeek LLM 客户端"""
    if not config.DEEPSEEK_API_KEY:
        raise ValueError(
            "未找到 DEEPSEEK_API_KEY！\n"
            "请设置环境变量：set DEEPSEEK_API_KEY=你的密钥"
        )
    client = OpenAI(
        api_key=config.DEEPSEEK_API_KEY,
        base_url=config.DEEPSEEK_BASE_URL,
    )
    logger.info("DeepSeek 客户端初始化成功")
    return client


def init_vector_db() -> FAISS:
    """加载 FAISS 向量库"""
    embeddings = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL_NAME)
    # 尝试加载
    try:
        db = FAISS.load_local(
            config.FAISS_INDEX_PATH,
            embeddings,
            allow_dangerous_deserialization=True,
        )
        logger.info("FAISS 向量库加载成功")
        return db
    except Exception as e:
        logger.error(f"加载向量库失败: {e}")
        # 如果不存在，可能是还没运行 ingest.py
        return None


def init_books_data() -> list:
    """加载图书 JSON 数据"""
    with open(config.BOOKS_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    logger.info(f"图书数据加载成功，共 {len(data)} 本")
    return data



# ============================================================
#  2. Agent 工具函数
# ============================================================

def query_book_location(book_name: str) -> str:
    """按书名或作者模糊搜索书籍位置和状态"""
    if books_data is None:
        return "图书馆图书数据库尚未加载。"
    
    keyword = book_name.strip().lower()
    if not keyword:
        return "请提供要查询的书名或作者。"

    title_matches = [
        b for b in books_data
        if keyword in b["title"].lower()
    ]
    author_matches = [
        b for b in books_data
        if keyword in b["author"].lower() and b not in title_matches
    ]

    results = (title_matches + author_matches)[:5]
    if results:
        return json.dumps(results, ensure_ascii=False)
    return f"图书库中未找到与「{book_name}」相关的书籍。"


def query_books_by_category(category: str) -> str:
    """按分类查询相关图书"""
    if books_data is None:
        return "图书馆图书数据库尚未加载。"

    keyword = category.strip().lower()
    if not keyword:
        return "请提供要查询的图书分类。"

    results = [
        b for b in books_data
        if keyword in b["category"].lower() or keyword in b["description"].lower()
    ][:5]

    if results:
        return json.dumps(results, ensure_ascii=False)
    return f"未找到与「{category}」相关的分类图书。"


def query_books_by_status(status: str) -> str:
    """按在馆状态查询图书"""
    if books_data is None:
        return "图书馆图书数据库尚未加载。"

    keyword = status.strip()
    if not keyword:
        return "请提供要查询的图书状态。"

    results = [
        b for b in books_data
        if keyword in b["status"]
    ][:5]

    if results:
        return json.dumps(results, ensure_ascii=False)
    return f"未找到状态为「{status}」的图书。"


def recommend_books(keyword: str) -> str:
    """根据关键词推荐图书"""
    if books_data is None:
        return "图书馆图书数据库尚未加载。"

    query = keyword.strip().lower()
    if not query:
        return "请提供推荐方向，例如：计算机、哲学、考研、人工智能。"

    results = [
        b for b in books_data
        if (
            query in b["title"].lower()
            or query in b["category"].lower()
            or query in b["description"].lower()
        )
    ][:5]

    if results:
        return json.dumps(results, ensure_ascii=False)
    return f"暂时没有找到与「{keyword}」相关的推荐图书。"


def query_library_rules(question: str) -> str:
    """查询馆内规章信息（基于 RAG 向量库）"""
    if vector_db is None:
        return "抱歉，规章制度知识库尚未初始化，暂时无法查询。"

    # 执行相似度搜索 (RAG 核心步骤)
    docs = vector_db.similarity_search(question, k=config.SIMILARITY_TOP_K)
    
    if not docs:
        return "在大规模规章文档中未找到直接相关的规定。"

    # 将检索到的分片合并
    context = "\n".join([f"· {d.page_content}" for d in docs])
    return f"【参考馆内规定】:\n{context}"


# ============================================================
#  3. 工具描述（供 DeepSeek Function Calling 识别）
# ============================================================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "query_book_location",
            "description": "按书名或作者查询图书的具体位置、架位、作者及在馆状态。当用户提到具体书名，或询问某位作者的书时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "book_name": {
                        "type": "string",
                        "description": "书籍名称或作者名称",
                    }
                },
                "required": ["book_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_books_by_category",
            "description": "按图书分类、学科方向或主题查询相关图书。当用户询问某一类图书、某学科图书时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "图书分类或主题关键词，如计算机、哲学、文学、历史",
                    }
                },
                "required": ["category"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_books_by_status",
            "description": "按图书状态查询图书。当用户关心图书是否在馆、已借出、是否仅限馆内阅览时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "图书状态，如在馆、已借出、仅限馆内阅览",
                    }
                },
                "required": ["status"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recommend_books",
            "description": "根据用户兴趣、方向或关键词推荐图书。当用户说推荐几本、想看什么方向的书时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "推荐关键词，如人工智能、考研、哲学、计算机",
                    }
                },
                "required": ["keyword"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_library_rules",
            "description": "查询图书馆的开放时间、借阅规则、入馆须知等非图书位置类信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "用户的具体问题",
                    }
                },
                "required": ["question"],
            },
        },
    },
]

# 工具名 → Python 函数 的映射表（方便扩展，避免大量 if-elif）
TOOL_FUNCTIONS = {
    "query_book_location": lambda args: query_book_location(args.get("book_name", "")),
    "query_books_by_category": lambda args: query_books_by_category(args.get("category", "")),
    "query_books_by_status": lambda args: query_books_by_status(args.get("status", "")),
    "recommend_books": lambda args: recommend_books(args.get("keyword", "")),
    "query_library_rules": lambda args: query_library_rules(args.get("question", "")),
}


# ============================================================
#  4. Agent 核心逻辑（支持多轮对话记忆）
# ============================================================

def _trim_chat_history(chat_history: list) -> list:
    """保留最近 N 轮对话，避免上下文无限增长。"""
    max_messages = config.MAX_HISTORY_ROUNDS * 2
    if len(chat_history) > max_messages:
        return chat_history[-max_messages:]
    return chat_history


def _parse_tool_result_as_books(content: str) -> list[dict[str, Any]]:
    """将工具返回的 JSON 结果解析为图书列表，便于前端渲染卡片。"""
    try:
        parsed = json.loads(content)
    except (TypeError, json.JSONDecodeError):
        return []

    if isinstance(parsed, list):
        return [item for item in parsed if isinstance(item, dict)]
    return []


def library_agent_with_meta(user_query: str, chat_history: list) -> dict[str, Any]:
    """
    Agent 主函数：接收用户问题 + 历史对话，返回回答及工具调用元数据。

    参数:
        user_query:   本轮用户输入
        chat_history: 历史对话列表，格式为 [{"role": "user/assistant", "content": "..."}]

    流程：
        system prompt
        + 历史对话（最近 N 轮）
        + 本轮用户问题
        → DeepSeek 判断是否调用工具
        → 执行工具
        → 生成回答
    """
    recent_history = _trim_chat_history(chat_history)

    # 拼装完整的 messages：system + 历史 + 本轮问题
    messages = (
        [{"role": "system", "content": config.SYSTEM_PROMPT}]
        + recent_history
        + [{"role": "user", "content": user_query}]
    )

    try:
        if client is None:
            return {
                "answer": "助手尚未初始化，请稍后再试。",
                "tool_results": [],
                "books": [],
            }

        # 第一步：发送问题和工具定义给 DeepSeek
        response = client.chat.completions.create(
            model=config.DEEPSEEK_MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )
    except Exception as e:
        logger.error(f"DeepSeek API 调用失败: {e}")
        return {
            "answer": f"抱歉，我暂时无法回答，网络可能出了点问题。（错误: {type(e).__name__}）",
            "tool_results": [],
            "books": [],
        }

    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls
    tool_results = []
    books = []

    # 第二步：如果 DeepSeek 要求调用工具
    if tool_calls:
        messages.append(response_message)

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            logger.info(f"调用工具: {function_name}")

            try:
                function_args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                logger.warning(f"工具参数解析失败: {tool_call.function.arguments}")
                function_args = {}

            # 通过映射表调用对应函数
            func = TOOL_FUNCTIONS.get(function_name)
            if func:
                content = func(function_args)
            else:
                content = f"未定义的工具: {function_name}"
                logger.warning(content)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": content,
            })

            tool_results.append({
                "name": function_name,
                "arguments": function_args,
                "content": content,
            })
            books.extend(_parse_tool_result_as_books(content))

        # 第三步：让 DeepSeek 根据工具结果生成自然语言回答
        try:
            if client is None:
                return {
                    "answer": "助手无法生成最终回答（未初始化）。",
                    "tool_results": tool_results,
                    "books": books,
                }
            
            final_response = client.chat.completions.create(
                model=config.DEEPSEEK_MODEL,
                messages=messages,
            )
            return {
                "answer": final_response.choices[0].message.content,
                "tool_results": tool_results,
                "books": books,
            }
        except Exception as e:
            logger.error(f"DeepSeek 第二次调用失败: {e}")
            return {
                "answer": "抱歉，生成回答时出了点问题，请再试一次。",
                "tool_results": tool_results,
                "books": books,
            }

    return {
        "answer": response_message.content,
        "tool_results": [],
        "books": [],
    }


def library_agent(user_query: str, chat_history: list) -> str:
    """兼容原 CLI 调用方式，只返回文本回答。"""
    return library_agent_with_meta(user_query, chat_history)["answer"]


# ============================================================
#  5. 主程序入口
# ============================================================

if __name__ == "__main__":
    # --- 初始化（全局组件赋值）---
    try:
        initialize_system()
    except FileNotFoundError as e:
        print(f"\n❌ 文件缺失: {e}")
        print("   请确保以下文件存在:")
        print(f"   - {config.BOOKS_JSON_PATH}")
        print(f"   - {config.FAISS_INDEX_PATH}/")
        print("   提示: 先运行 python ingest.py 构建向量库")
        exit(1)
    except ValueError as e:
        print(f"\n❌ 配置错误: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ 初始化失败: {type(e).__name__}: {e}")
        exit(1)

    # --- TTS 开关 ---
    tts_enabled = True

    # --- 对话历史记忆 ---
    chat_history = []  # 存储 {"role": "user/assistant", "content": "..."}

    # --- 欢迎信息 ---
    print("=" * 50)
    print("  📚 智能图书馆语音助手已启动")
    print("  输入 'exit' 退出")
    print("  输入 'tts on' / 'tts off' 开关语音")
    print("  输入 'clear' 清除对话记忆")
    print("=" * 50)

    if tts_enabled:
        speak("欢迎来到智能图书馆，我是你的语音助手，请问有什么可以帮你的？")

    # --- 主循环 ---
    while True:
        try:
            query = input("\n学生: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n👋 再见！")
            break

        if query == "exit":
            if tts_enabled:
                speak("再见，祝你学习愉快！")
            print("👋 再见！")
            break

        if query == "tts on":
            tts_enabled = True
            print("🔊 语音已开启")
            speak("语音功能已开启")
            continue
        elif query == "tts off":
            tts_enabled = False
            print("🔇 语音已关闭")
            continue
        elif query == "clear":
            chat_history.clear()
            print("🗑️ 对话记忆已清除，可以开始新的对话了")
            continue

        if not query:
            continue

        # 调用 Agent 获取回答（传入历史对话）
        ans = library_agent(query, chat_history)
        print(f"助手: {ans}\n")

        # 将本轮对话追加到历史记录 (只有当 Agent 成功回答时)
        if ans and not ans.startswith("抱歉，我暂时无法回答"):
            chat_history.append({"role": "user", "content": query})
            chat_history.append({"role": "assistant", "content": ans})

        if tts_enabled:
            speak(ans)
