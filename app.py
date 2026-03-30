import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from starlette.background import BackgroundTask

import main
import tts


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_FILE = os.path.join(BASE_DIR, "index.html")

app = FastAPI(title="Library Assistant Web API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

system_ready = False


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = Field(default_factory=list)


class TTSRequest(BaseModel):
    text: str


def _safe_remove_file(path: str) -> None:
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


def ensure_system_initialized() -> None:
    global system_ready

    if system_ready:
        return

    try:
        main.initialize_system()
        system_ready = True
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "System initialization failed. "
                "Please check DEEPSEEK_API_KEY, data files, and model cache permissions. "
                f"Original error: {exc}"
            ),
        ) from exc


@app.get("/api/health")
async def health_check():
    try:
        ensure_system_initialized()
        return {"status": "ok", "system_ready": True}
    except HTTPException as exc:
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "system_ready": False,
                "detail": exc.detail,
            },
        )


@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        ensure_system_initialized()
        return main.library_agent_with_meta(request.message, request.history)
    except Exception as exc:
        print(f"Error in chat endpoint: {exc}")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/tts")
async def text_to_speech(request: TTSRequest):
    text = request.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")

    try:
        ensure_system_initialized()
        output_file = await tts.synthesize_to_file_async(text)
        if not output_file or not os.path.exists(output_file):
            raise HTTPException(status_code=500, detail="Failed to generate audio")

        return FileResponse(
            output_file,
            media_type="audio/mpeg",
            filename="speech.mp3",
            background=BackgroundTask(_safe_remove_file, output_file),
        )
    except HTTPException:
        raise
    except Exception as exc:
        print(f"Error in TTS endpoint: {exc}")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/")
async def read_index():
    if not os.path.exists(INDEX_FILE):
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(INDEX_FILE)


if __name__ == "__main__":
    import uvicorn

    print("=" * 50)
    print("系统启动中...")
    print("请在浏览器访问: http://localhost:8000")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8000)
