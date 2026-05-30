from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from pydub import AudioSegment


class DubDeckError(RuntimeError):
    pass


def run_command(command: list[str], friendly_error: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(command, check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise DubDeckError("FFmpeg is not installed or is not available in PATH.") from exc
    except subprocess.CalledProcessError as exc:
        details = exc.stderr.strip() or exc.stdout.strip()
        raise DubDeckError(f"{friendly_error}\n\nDetails: {details}") from exc


def ensure_folders(project_dir: Path) -> None:
    for folder in ["input", "output", "temp", "assets"]:
        (project_dir / folder).mkdir(parents=True, exist_ok=True)


def check_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def require_ffmpeg() -> None:
    if not check_ffmpeg():
        raise DubDeckError("FFmpeg is not installed. Install FFmpeg and restart DubDeck AI.")


def video_duration(video_path: Path) -> float:
    require_ffmpeg()
    result = run_command(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(video_path),
        ],
        "Could not read video duration.",
    )
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])


def has_audio_stream(video_path: Path) -> bool:
    require_ffmpeg()
    result = run_command(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "a",
            "-show_entries",
            "stream=index",
            "-of",
            "csv=p=0",
            str(video_path),
        ],
        "Could not check video audio stream.",
    )
    return bool(result.stdout.strip())


def audio_duration(audio_path: Path) -> float:
    require_ffmpeg()
    result = run_command(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(audio_path),
        ],
        "Could not read audio duration.",
    )
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])


def extract_audio(video_path: Path, output_audio: Path) -> Path:
    require_ffmpeg()
    output_audio.parent.mkdir(parents=True, exist_ok=True)
    run_command(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            str(output_audio),
        ],
        "Audio extraction failed.",
    )
    return output_audio


def convert_audio(input_audio: Path, output_audio: Path) -> Path:
    require_ffmpeg()
    run_command(
        ["ffmpeg", "-y", "-i", str(input_audio), str(output_audio)],
        "Audio conversion failed.",
    )
    return output_audio


def merge_audio_with_video(video_path: Path, audio_path: Path, output_video: Path) -> Path:
    require_ffmpeg()
    output_video.parent.mkdir(parents=True, exist_ok=True)
    run_command(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-i",
            str(audio_path),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-shortest",
            str(output_video),
        ],
        "Final MP4 export failed.",
    )
    if not output_video.exists():
        raise DubDeckError("Output file was not created.")
    return output_video


def separate_music_with_demucs(audio_path: Path, temp_dir: Path) -> tuple[Path, Path]:
    temp_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = temp_dir.parent / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "demucs",
        "--two-stems",
        "vocals",
        "-o",
        str(temp_dir),
        str(audio_path),
    ]
    env = os.environ.copy()
    env["TORCH_HOME"] = str(cache_dir / "torch")
    env["XDG_CACHE_HOME"] = str(cache_dir)
    env["HF_HOME"] = str(cache_dir / "huggingface")
    env["HUGGINGFACE_HUB_CACHE"] = str(cache_dir / "huggingface" / "hub")
    env["TRANSFORMERS_CACHE"] = str(cache_dir / "huggingface" / "transformers")
    env["PYTHONPYCACHEPREFIX"] = str(cache_dir / "pycache")
    try:
        subprocess.run(command, check=True, capture_output=True, text=True, env=env)
    except subprocess.CalledProcessError as exc:
        details = exc.stderr.strip() or exc.stdout.strip()
        raise DubDeckError(f"Demucs music separation failed.\n\nDetails: {details}") from exc

    stem_dir = temp_dir / "htdemucs" / audio_path.stem
    vocals = stem_dir / "vocals.wav"
    music = stem_dir / "no_vocals.wav"
    if not vocals.exists() or not music.exists():
        raise DubDeckError("Demucs finished, but separated audio files were not found.")
    return vocals, music


def create_silence(duration_seconds: float) -> AudioSegment:
    return AudioSegment.silent(duration=int(duration_seconds * 1000), frame_rate=44100)


def mix_voice_with_music(
    voice_path: Path,
    music_path: Path | None,
    output_path: Path,
    voice_segments: list[tuple[float, float]],
    video_duration_seconds: float,
) -> Path:
    voice = AudioSegment.from_file(voice_path).set_frame_rate(44100).set_channels(2)
    base_duration_ms = int(video_duration_seconds * 1000)

    if music_path and music_path.exists():
        music = AudioSegment.from_file(music_path).set_frame_rate(44100).set_channels(2)
        if len(music) < base_duration_ms:
            repeats = int(base_duration_ms / max(1, len(music))) + 1
            music = music * repeats
        music = music[:base_duration_ms] - 22

        for start, end in voice_segments:
            start_ms = max(0, int(start * 1000))
            end_ms = min(base_duration_ms, int(end * 1000))
            if end_ms <= start_ms:
                continue
            music = music[:start_ms] + (music[start_ms:end_ms] - 12) + music[end_ms:]
    else:
        music = create_silence(video_duration_seconds).set_channels(2)

    mixed = music.overlay(voice)
    mixed.export(output_path, format="wav")
    return output_path
