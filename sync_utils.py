from __future__ import annotations

import asyncio
from pathlib import Path

import edge_tts
from pydub import AudioSegment

from audio_utils import audio_duration, create_silence
from subtitle_utils import Segment, seconds_to_srt_time


SYNC_RATES = ["-5%", "+0%", "+5%", "+10%", "+15%", "+20%"]


class TTSError(RuntimeError):
    pass


def style_to_rate(style: str) -> str:
    if style == "Slow Training Voice":
        return "-10%"
    if style == "Natural":
        return "-5%"
    return "-5%"


async def _edge_tts_save(text: str, voice: str, rate: str, output_path: Path) -> None:
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate)
    await communicate.save(str(output_path))


def generate_tts(text: str, voice: str, rate: str, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        asyncio.run(_edge_tts_save(text, voice, rate, output_path))
    except Exception as exc:  # edge-tts exposes several network/runtime errors.
        raise TTSError(f"edge-tts voice generation failed: {exc}") from exc
    if not output_path.exists():
        raise TTSError("Hindi voice file was not created.")
    return output_path


def place_segments_on_timeline(
    segments: list[Segment],
    video_duration_seconds: float,
    voice: str,
    temp_dir: Path,
    output_voice_path: Path,
) -> tuple[Path, list[Segment], list[Segment]]:
    timeline = create_silence(video_duration_seconds)
    manual_fix: list[Segment] = []
    temp_dir.mkdir(parents=True, exist_ok=True)

    for segment in segments:
        clean_text = segment.hindi.strip()
        if not clean_text:
            segment.fit_status = "Manual fix"
            segment.problem = "Hindi text is empty"
            manual_fix.append(segment)
            continue

        selected_audio: Path | None = None
        selected_rate = ""
        used_adjustment = False
        for rate in SYNC_RATES:
            candidate = temp_dir / f"segment_{segment.number:04}_{rate.replace('%', 'pct').replace('+', 'plus')}.mp3"
            generate_tts(clean_text, voice, rate, candidate)
            duration = audio_duration(candidate)
            if duration <= segment.duration + 0.08:
                selected_audio = candidate
                selected_rate = rate
                used_adjustment = rate not in ("-5%", "+0%")
                break

        if selected_audio is None:
            segment.fit_status = "Manual fix"
            segment.rate_used = "+20%"
            segment.problem = "Hindi audio too long even at +20%"
            manual_fix.append(segment)
            selected_audio = candidate
        else:
            segment.fit_status = "Speed adjusted" if used_adjustment else "Perfect"
            segment.rate_used = selected_rate

        audio = AudioSegment.from_file(selected_audio)
        timeline = timeline.overlay(audio, position=int(segment.start * 1000))

    timeline.export(output_voice_path, format="wav")
    return output_voice_path, segments, manual_fix


def write_needs_manual_fix(path: Path, segments: list[Segment]) -> None:
    if not segments:
        path.write_text("No manual fixes needed.\n", encoding="utf-8")
        return

    lines = ["Segments needing manual fix", ""]
    for segment in segments:
        lines.extend(
            [
                f"Segment {segment.number} | {seconds_to_srt_time(segment.start)} --> {seconds_to_srt_time(segment.end)}",
                f"English: {segment.english}",
                f"Hindi: {segment.hindi}",
                f"Problem: {segment.problem}",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def create_sync_report(
    path: Path,
    input_name: str,
    video_duration_seconds: float,
    segments: list[Segment],
    manual_fix_segments: list[Segment],
) -> None:
    total = len(segments)
    perfect = sum(1 for segment in segments if segment.fit_status == "Perfect")
    adjusted = sum(1 for segment in segments if segment.fit_status == "Speed adjusted")
    manual = len(manual_fix_segments)
    score = round(((perfect + adjusted) / total) * 100) if total else 0

    lines = [
        "DubDeck AI Sync Report",
        "",
        f"Input file: {input_name}",
        f"Video duration: {seconds_to_srt_time(video_duration_seconds).replace(',', '.')}",
        f"Total segments: {total}",
        f"Perfectly fitted: {perfect}",
        f"Speed adjusted: {adjusted}",
        f"Manual fix needed: {manual}",
        f"Final sync score: {score}%",
        "",
        "Manual fix segments:",
    ]
    if manual_fix_segments:
        for segment in manual_fix_segments:
            lines.extend(
                [
                    f"Segment {segment.number} | {seconds_to_srt_time(segment.start)} --> {seconds_to_srt_time(segment.end)}",
                    f"English: {segment.english}",
                    f"Hindi: {segment.hindi}",
                    f"Problem: {segment.problem}",
                    "",
                ]
            )
    else:
        lines.append("None")
    path.write_text("\n".join(lines), encoding="utf-8")
