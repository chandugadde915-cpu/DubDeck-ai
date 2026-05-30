from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import edge_tts
from pydub import AudioSegment

from audio_utils import audio_duration, create_silence
from subtitle_utils import Segment, seconds_to_srt_time


SYNC_RATES = ["-10%", "-5%", "+0%", "+5%", "+10%"]
MAX_SPEED_RATIO = 1.22


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
    if output_path.exists() and output_path.stat().st_size > 0:
        return output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        asyncio.run(_edge_tts_save(text, voice, rate, output_path))
    except Exception as exc:  # edge-tts exposes several network/runtime errors.
        raise TTSError(f"edge-tts voice generation failed: {exc}") from exc
    if not output_path.exists():
        raise TTSError("Hindi voice file was not created.")
    return output_path


def _speed_change(sound: AudioSegment, ratio: float) -> AudioSegment:
    if ratio <= 1.01:
        return sound
    shifted = sound._spawn(sound.raw_data, overrides={"frame_rate": int(sound.frame_rate * ratio)})
    return shifted.set_frame_rate(sound.frame_rate)


def _fit_audio_to_segment(audio: AudioSegment, target_seconds: float) -> tuple[AudioSegment, float, str]:
    target_ms = max(1, int(target_seconds * 1000))
    duration_ms = len(audio)
    if duration_ms <= target_ms:
        return audio + AudioSegment.silent(duration=target_ms - duration_ms, frame_rate=audio.frame_rate), 1.0, "Perfect"

    ratio = duration_ms / target_ms
    if ratio <= MAX_SPEED_RATIO:
        fitted = _speed_change(audio, ratio)
        if len(fitted) > target_ms:
            fitted = fitted[:target_ms]
        else:
            fitted += AudioSegment.silent(duration=target_ms - len(fitted), frame_rate=fitted.frame_rate)
        return fitted, ratio, "Speed adjusted"

    fitted = _speed_change(audio, MAX_SPEED_RATIO)
    if len(fitted) > target_ms:
        fitted = fitted[:target_ms]
    else:
        fitted += AudioSegment.silent(duration=target_ms - len(fitted), frame_rate=fitted.frame_rate)
    return fitted, MAX_SPEED_RATIO, "Manual fix"


def _generate_segment_candidate(segment: Segment, voice: str, temp_dir: Path) -> Path:
    rate = "-5%"
    output = temp_dir / f"segment_{segment.number:04}_{rate.replace('%', 'pct').replace('-', 'minus')}.mp3"
    last_error: Exception | None = None
    for _attempt in range(2):
        try:
            return generate_tts(segment.hindi.strip(), voice, rate, output)
        except Exception as exc:
            last_error = exc
    raise TTSError(f"TTS failed for segment {segment.number}. Retrying did not recover. {last_error}")


def place_segments_on_timeline(
    segments: list[Segment],
    video_duration_seconds: float,
    voice: str,
    temp_dir: Path,
    output_voice_path: Path,
    auto_speed_fit: bool = True,
    enable_cache: bool = True,
    parallel_tts: bool = False,
    progress=None,
) -> tuple[Path, list[Segment], list[Segment]]:
    timeline = create_silence(video_duration_seconds)
    manual_fix: list[Segment] = []
    temp_dir.mkdir(parents=True, exist_ok=True)

    generated: dict[int, Path] = {}
    tts_segments = [segment for segment in segments if segment.hindi.strip()]

    if parallel_tts and tts_segments:
        workers = min(4, len(tts_segments))
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(_generate_segment_candidate, segment, voice, temp_dir): segment for segment in tts_segments}
            for done, future in enumerate(as_completed(futures), start=1):
                segment = futures[future]
                try:
                    generated[segment.number] = future.result()
                    if progress:
                        progress("Generating Hindi voice", "Running", done, len(tts_segments), f"Generated TTS segment {done}/{len(tts_segments)}")
                except Exception as exc:
                    segment.fit_status = "Manual fix"
                    segment.problem = f"TTS failed: {exc}"
                    manual_fix.append(segment)

    for index, segment in enumerate(segments, start=1):
        clean_text = segment.hindi.strip()
        if not clean_text:
            segment.fit_status = "Manual fix"
            segment.problem = "Hindi text is empty"
            manual_fix.append(segment)
            continue

        selected_audio = generated.get(segment.number)
        if selected_audio is None:
            selected_audio = _generate_segment_candidate(segment, voice, temp_dir)
            if progress:
                progress("Generating Hindi voice", "Running", index, len(segments), f"Generated TTS segment {index}/{len(segments)}")

        audio = AudioSegment.from_file(selected_audio).set_frame_rate(44100).set_channels(1)
        if auto_speed_fit:
            fitted, ratio, status = _fit_audio_to_segment(audio, segment.duration)
        else:
            target_ms = max(1, int(segment.duration * 1000))
            fitted = audio[:target_ms] if len(audio) > target_ms else audio + AudioSegment.silent(duration=target_ms - len(audio), frame_rate=audio.frame_rate)
            ratio = 1.0
            status = "Manual fix" if len(audio) > target_ms else "Perfect"

        fitted_path = temp_dir / f"segment_{segment.number:04}_fitted.wav"
        fitted.export(fitted_path, format="wav")
        segment.generated_audio = str(fitted_path)
        segment.final_duration = len(fitted) / 1000
        segment.speed_ratio = round(ratio, 3)
        segment.rate_used = f"{ratio:.2f}x"
        segment.fit_status = status
        if status == "Speed adjusted":
            segment.problem = "Hindi segment exceeded original duration. Speed adjusted."
        elif status == "Manual fix":
            segment.problem = "Hindi audio too long; fitted with max safe speed and trimmed."
            if segment not in manual_fix:
                manual_fix.append(segment)

        timeline = timeline.overlay(fitted, position=int(segment.start * 1000))

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
