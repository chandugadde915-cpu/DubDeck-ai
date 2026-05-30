from __future__ import annotations

import shutil
from pathlib import Path
from typing import Callable

from faster_whisper import WhisperModel

from audio_utils import (
    DubDeckError,
    audio_duration,
    ensure_folders,
    extract_audio,
    has_audio_stream,
    merge_audio_with_video,
    mix_voice_with_music,
    separate_music_with_demucs,
    video_duration,
)
from subtitle_utils import Segment, write_srt
from sync_utils import create_sync_report, generate_tts, place_segments_on_timeline, style_to_rate, write_needs_manual_fix
from translate_utils import TranslationError, translate_with_glossary


Progress = Callable[[str, str], None]


def _progress(callback: Progress | None, step: str, status: str) -> None:
    if callback:
        callback(step, status)


def _load_whisper(model_name: str = "base") -> WhisperModel:
    return WhisperModel(model_name, device="cpu", compute_type="int8")


def _copy_input(input_video: Path, project_dir: Path) -> Path:
    target = project_dir / "input" / "input.mp4"
    if input_video.resolve() != target.resolve():
        shutil.copy2(input_video, target)
    return target


def transcribe_full(audio_path: Path, progress: Progress | None = None) -> str:
    _progress(progress, "Transcribing English speech", "Running")
    model = _load_whisper()
    segments, _info = model.transcribe(str(audio_path), language="en", vad_filter=True)
    text = " ".join(segment.text.strip() for segment in segments).strip()
    if not text:
        raise DubDeckError("Whisper transcription failed or no English speech was detected.")
    _progress(progress, "Transcribing English speech", "Completed")
    return text


def transcribe_segments(audio_path: Path, progress: Progress | None = None) -> list[Segment]:
    _progress(progress, "Transcribing English speech", "Running")
    model = _load_whisper()
    whisper_segments, _info = model.transcribe(str(audio_path), language="en", vad_filter=True, word_timestamps=False)
    segments = [
        Segment(number=index, start=item.start, end=item.end, english=item.text.strip())
        for index, item in enumerate(whisper_segments, start=1)
        if item.text.strip()
    ]
    if not segments:
        raise DubDeckError("Whisper transcription failed or no English speech was detected.")
    _progress(progress, "Transcribing English speech", "Completed")
    return segments


def quick_prepare(input_video: Path, project_dir: Path, progress: Progress | None = None) -> dict[str, Path]:
    ensure_folders(project_dir)
    input_copy = _copy_input(input_video, project_dir)
    output_dir = project_dir / "output"
    temp_dir = project_dir / "temp"
    glossary_path = project_dir / "maritime_glossary.txt"
    log_path = output_dir / "quick_dub_log.txt"

    try:
        _progress(progress, "Checking input video", "Running")
        if input_copy.suffix.lower() != ".mp4":
            raise DubDeckError("No MP4 uploaded. Please upload an .mp4 video.")
        if not has_audio_stream(input_copy):
            raise DubDeckError("Audio detected: no. Please upload a video with an English audio track.")
        _progress(progress, "Checking input video", "Completed")

        _progress(progress, "Extracting audio", "Running")
        audio_path = extract_audio(input_copy, temp_dir / "quick_original_audio.wav")
        _progress(progress, "Extracting audio", "Completed")

        english = transcribe_full(audio_path, progress)
        english_path = output_dir / "english_transcript.txt"
        english_path.write_text(english, encoding="utf-8")

        _progress(progress, "Translating to Hindi", "Running")
        hindi = translate_with_glossary(english, glossary_path)
        hindi_path = output_dir / "hindi_voiceover_script_for_tts.txt"
        hindi_path.write_text(hindi, encoding="utf-8")
        _progress(progress, "Translating to Hindi", "Completed")
        _progress(progress, "Waiting for Hindi script review", "Running")
        log_path.write_text("Quick Dub preparation completed. Waiting for review.\n", encoding="utf-8")
        return {"input_video": input_copy, "english": english_path, "hindi": hindi_path, "log": log_path}
    except (DubDeckError, TranslationError) as exc:
        log_path.write_text(f"Quick Dub failed: {exc}\n", encoding="utf-8")
        raise


def quick_render(
    input_video: Path,
    hindi_script: str,
    project_dir: Path,
    voice: str,
    speech_style: str,
    progress: Progress | None = None,
) -> dict[str, Path]:
    output_dir = project_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / "quick_dub_log.txt"

    try:
        _progress(progress, "Generating Hindi voice", "Running")
        hindi_path = output_dir / "hindi_voiceover_script_for_tts.txt"
        hindi_path.write_text(hindi_script, encoding="utf-8")
        voice_path = output_dir / "hindi_voiceover_single.mp3"
        generate_tts(hindi_script, voice, style_to_rate(speech_style), voice_path)
        _progress(progress, "Generating Hindi voice", "Completed")

        _progress(progress, "Exporting final video", "Running")
        output_video = output_dir / "output_hindi_quick.mp4"
        merge_audio_with_video(input_video, voice_path, output_video)
        _progress(progress, "Exporting final video", "Completed")
        log_path.write_text("Quick Dub completed successfully.\n", encoding="utf-8")
        return {"output_video": output_video, "voice": voice_path, "hindi": hindi_path, "log": log_path}
    except Exception as exc:
        log_path.write_text(f"Quick Dub export failed: {exc}\n", encoding="utf-8")
        raise


def quick_dub(input_video: Path, project_dir: Path, voice: str, speech_style: str, progress: Progress | None = None) -> dict[str, Path]:
    prepared = quick_prepare(input_video, project_dir, progress)
    hindi_script = prepared["hindi"].read_text(encoding="utf-8")
    return quick_render(prepared["input_video"], hindi_script, project_dir, voice, speech_style, progress)


def pro_prepare(
    input_video: Path,
    project_dir: Path,
    music_handling: str,
    progress: Progress | None = None,
) -> dict[str, Path | list[Segment]]:
    ensure_folders(project_dir)
    input_copy = _copy_input(input_video, project_dir)
    output_dir = project_dir / "output"
    temp_dir = project_dir / "temp"
    glossary_path = project_dir / "maritime_glossary.txt"
    log_path = output_dir / "pro_sync_log.txt"
    demucs_warning = ""

    try:
        _progress(progress, "Checking input video", "Running")
        if input_copy.suffix.lower() != ".mp4":
            raise DubDeckError("No MP4 uploaded. Please upload an .mp4 video.")
        if not has_audio_stream(input_copy):
            raise DubDeckError("Audio detected: no. Please upload a video with an English audio track.")
        _progress(progress, "Checking input video", "Completed")

        _progress(progress, "Extracting audio", "Running")
        audio_path = extract_audio(input_copy, temp_dir / "pro_original_audio.wav")
        _progress(progress, "Extracting audio", "Completed")

        music_path: Path | None = None
        if music_handling == "Keep original background music":
            _progress(progress, "Separating background music", "Running")
            try:
                _vocals, music_path = separate_music_with_demucs(audio_path, temp_dir / "demucs")
                _progress(progress, "Separating background music", "Completed")
            except DubDeckError as exc:
                demucs_warning = (
                    "Demucs background music separation failed, so Pro Sync will continue without original background music. "
                    "You can also choose Remove background music or Add new background music."
                )
                _progress(progress, "Separating background music", "Skipped")
                log_path.write_text(f"{demucs_warning}\n\nDetails: {exc}\n", encoding="utf-8")

        segments = transcribe_segments(audio_path, progress)
        english_srt = output_dir / "english_timed_transcript.srt"
        write_srt(english_srt, segments, language="english")

        _progress(progress, "Translating to Hindi", "Running")
        for segment in segments:
            segment.hindi = translate_with_glossary(segment.english, glossary_path)
        hindi_srt = output_dir / "hindi_timed_script.srt"
        write_srt(hindi_srt, segments, language="hindi")
        _progress(progress, "Translating to Hindi", "Completed")
        _progress(progress, "Waiting for Hindi script review", "Running")
        log_message = "Pro Sync preparation completed. Waiting for review.\n"
        if demucs_warning:
            log_message += f"\nMusic note: {demucs_warning}\n"
        log_path.write_text(log_message, encoding="utf-8")
        result: dict[str, Path | list[Segment]] = {
            "input_video": input_copy,
            "audio": audio_path,
            "english_srt": english_srt,
            "hindi_srt": hindi_srt,
            "segments": segments,
            "log": log_path,
        }
        if music_path:
            result["music"] = music_path
        if demucs_warning:
            result["music_warning"] = demucs_warning
        return result
    except (DubDeckError, TranslationError) as exc:
        log_path.write_text(f"Pro Sync failed: {exc}\n", encoding="utf-8")
        raise


def pro_render(
    input_video: Path,
    segments: list[Segment],
    project_dir: Path,
    voice: str,
    music_handling: str,
    background_music_path: Path | None,
    separated_music_path: Path | None,
    progress: Progress | None = None,
) -> dict[str, Path]:
    output_dir = project_dir / "output"
    temp_dir = project_dir / "temp"
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / "pro_sync_log.txt"

    try:
        video_len = video_duration(input_video)
        hindi_srt = output_dir / "hindi_timed_script.srt"
        write_srt(hindi_srt, segments, language="hindi")

        _progress(progress, "Generating Hindi voice", "Running")
        final_voice = output_dir / "final_hindi_voice.wav"
        final_voice, updated_segments, manual_fix = place_segments_on_timeline(
            segments,
            video_len,
            voice,
            temp_dir / "tts_segments",
            final_voice,
        )
        _progress(progress, "Generating Hindi voice", "Completed")

        _progress(progress, "Syncing Hindi voice to video timeline", "Completed")
        needs_manual_fix = output_dir / "needs_manual_fix.txt"
        write_needs_manual_fix(needs_manual_fix, manual_fix)

        _progress(progress, "Mixing background music", "Running")
        music_path = None
        if music_handling == "Keep original background music":
            music_path = separated_music_path
        elif music_handling == "Add new background music":
            music_path = background_music_path
        final_mixed = output_dir / "final_mixed_audio.wav"
        mix_voice_with_music(
            final_voice,
            music_path,
            final_mixed,
            [(segment.start, segment.end) for segment in updated_segments],
            video_len,
        )
        _progress(progress, "Mixing background music", "Completed")

        _progress(progress, "Exporting final video", "Running")
        output_video = output_dir / "output_hindi_synced.mp4"
        merge_audio_with_video(input_video, final_mixed, output_video)
        _progress(progress, "Exporting final video", "Completed")

        report = output_dir / "sync_report.txt"
        create_sync_report(report, input_video.name, video_len, updated_segments, manual_fix)
        log_path.write_text("Pro Sync completed successfully.\n", encoding="utf-8")
        return {
            "output_video": output_video,
            "final_voice": final_voice,
            "final_mixed": final_mixed,
            "hindi_srt": hindi_srt,
            "report": report,
            "needs_manual_fix": needs_manual_fix,
            "log": log_path,
        }
    except Exception as exc:
        log_path.write_text(f"Pro Sync export failed: {exc}\n", encoding="utf-8")
        raise


def pro_sync_dub(
    input_video: Path,
    project_dir: Path,
    voice: str,
    music_handling: str,
    background_music_path: Path | None = None,
    progress: Progress | None = None,
) -> dict[str, Path]:
    prepared = pro_prepare(input_video, project_dir, music_handling, progress)
    return pro_render(
        prepared["input_video"],  # type: ignore[arg-type]
        prepared["segments"],  # type: ignore[arg-type]
        project_dir,
        voice,
        music_handling,
        background_music_path,
        prepared.get("music"),  # type: ignore[arg-type]
        progress,
    )


def dry_run_check(project_dir: Path) -> list[str]:
    ensure_folders(project_dir)
    checks = ["Folders ready"]
    try:
        from audio_utils import check_ffmpeg

        checks.append("FFmpeg ready" if check_ffmpeg() else "FFmpeg missing")
    except Exception:
        checks.append("FFmpeg check failed")
    return checks
