"""
tts.py - TTS 语音合成模块

使用 Edge-TTS（微软免费服务）将文字转为语音并播放。
同时为 Web 前端提供“只生成音频文件、不本地播放”的能力。
"""

import asyncio
import logging
import os
import platform
import subprocess
import uuid

import edge_tts

import config

logger = logging.getLogger(__name__)


async def _text_to_speech_async(
    text: str,
    output_file: str,
    rate: str = "+0%",
    volume: str = "+0%",
):
    """异步将文字转为语音并保存为 MP3 文件"""
    communicate = edge_tts.Communicate(text, config.TTS_VOICE, rate=rate, volume=volume)
    await communicate.save(output_file)


async def synthesize_to_file_async(
    text: str,
    output_file: str | None = None,
    output_dir: str | None = None,
    rate: str = "+0%",
    volume: str = "+0%",
) -> str | None:
    """【异步版】将文本合成为音频文件，返回生成后的文件路径。"""
    if not text or not text.strip():
        return None

    if output_file is None:
        base_dir = output_dir or os.path.dirname(config.TTS_OUTPUT_FILE)
        os.makedirs(base_dir, exist_ok=True)
        output_file = os.path.join(base_dir, f"tts_{uuid.uuid4().hex}.mp3")
    else:
        os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)

    await _text_to_speech_async(text, output_file, rate, volume)
    return output_file


def synthesize_to_file(
    text: str,
    output_file: str | None = None,
    output_dir: str | None = None,
    rate: str = "+0%",
    volume: str = "+0%",
) -> str | None:
    """【同步版】将文本合成为音频文件，返回生成后的文件路径。"""
    try:
        # 尝试获取当前运行的事件循环
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # 如果没有运行中的循环，可以使用 asyncio.run
        return asyncio.run(synthesize_to_file_async(text, output_file, output_dir, rate, volume))
    else:
        # 如果有运行中的循环，直接调用 asyncio.run 会报错
        # 这种情况下通常建议调用异步版本的函数
        raise RuntimeError(
            "Detected a running event loop. Please use 'synthesize_to_file_async' instead of 'synthesize_to_file'."
        )


def speak(text: str, rate: str = "+0%", volume: str = "+0%"):
    """
    【主要接口】将文字转为语音并播放

    参数:
        text:   要朗读的文字
        rate:   语速调整，如 "+20%" 加快，"-10%" 减慢
        volume: 音量调整，如 "+50%" 增大
    """
    if not text or not text.strip():
        return

    print("🔊 语音合成中...")

    try:
        output_file = synthesize_to_file(
            text,
            output_file=config.TTS_OUTPUT_FILE,
            rate=rate,
            volume=volume,
        )
    except Exception as e:
        logger.warning(f"语音合成失败: {e}")
        print("⚠️ 语音合成失败，跳过播放")
        return

    if output_file:
        _play_audio(output_file)


def _play_audio(filepath: str):
    """
    跨平台播放音频文件
    - Windows: 优先使用 pygame，备选 PowerShell
    - macOS:   使用 afplay
    - Linux:   使用 mpv 或 ffplay
    """
    if not os.path.exists(filepath):
        logger.warning(f"音频文件不存在: {filepath}")
        return

    system = platform.system()

    try:
        if system == "Windows":
            _play_windows(filepath)
        elif system == "Darwin":
            subprocess.run(["afplay", filepath], timeout=120)
        else:
            _play_linux(filepath)
    except Exception as e:
        print(f"⚠️ 播放语音时出错: {e}")
        print(f"   语音文件已保存至: {filepath}，你可以手动打开播放")


def _play_windows(filepath: str):
    """Windows 平台播放音频"""
    # 优先使用 pygame
    try:
        import pygame
        pygame.mixer.init()
        pygame.mixer.music.load(filepath)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.wait(100)
        pygame.mixer.music.stop()
        pygame.mixer.quit()
        return
    except ImportError:
        logger.info("pygame 未安装，使用 PowerShell 播放")
    except Exception as e:
        logger.warning(f"pygame 播放失败: {e}，尝试 PowerShell")

    # 备选：PowerShell MediaPlayer
    subprocess.run(
        ["powershell", "-c", f"""
        Add-Type -AssemblyName presentationCore
        $player = New-Object System.Windows.Media.MediaPlayer
        $player.Open('{filepath}')
        $player.Play()
        Start-Sleep -Seconds ([math]::Ceiling($player.NaturalDuration.TimeSpan.TotalSeconds) + 1)
        $player.Close()
        """],
        capture_output=True,
        timeout=120,
    )


def _play_linux(filepath: str):
    """Linux 平台播放音频"""
    for cmd in ["mpv --no-video", "ffplay -nodisp -autoexit"]:
        try:
            subprocess.run(cmd.split() + [filepath], timeout=120)
            return
        except FileNotFoundError:
            continue
    print("⚠️ 未找到音频播放器，请安装 mpv: sudo apt install mpv")


# --- 测试 ---
if __name__ == "__main__":
    print("正在测试语音合成...\n")
    speak("欢迎来到智能图书馆！我是你的语音助手，有什么可以帮你的吗？")
    print("✅ 测试完成！")
