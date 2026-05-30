from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Callable, Any

from faster_whisper import WhisperModel

from audio_utils import (
    DubDeckError,
    audio_duration,
    ensure_folders,
    extract_audio,
    extract_audio_for_mixing,
    has_audio_stream,
    merge_audio_with_video,
    mix_voice_with_music,
    separate_music_with_demucs,
    video_duration,
)
from subtitle_utils import Segment, dict_to_segment, segment_to_dict, write_srt
from sync_utils import create_sync_report, generate_tts, place_segments_on_timeline, style_to_rate, write_needs_manual_fix
from translate_utils import TranslationError, translate_segments_with_glossary, translate_with_glossary


Progress = Callable[..., None]


def _progress(callback: Progress | None, step: str, status: str, *details: Any) -> None:
    if callback:
        callback(step, status, *details)


def _file_progress(callback: Progress | None, log_path: Path) -> Progress:
    def report(step: str, status: str, *details: Any) -> None:
        message = ""
        if len(details) >= 3 and isinstance(details[2], str):
            message = details[2]
        line = f"{step}: {status}"
        if message:
            line += f" - {message}"
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        if callback:
            callback(step, status, *details)

    return report


def _load_whisper(model_name: str = "small") -> WhisperModel:
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


def transcribe_segments(audio_path: Path, progress: Progress | None = None, model_name: str = "small") -> list[Segment]:
    _progress(progress, "Transcribing English speech", "Running")
    model = _load_whisper(model_name)
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


def _write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_segments_json(path: Path) -> list[Segment]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [dict_to_segment(item) for item in data]


def _write_segments_json(path: Path, segments: list[Segment]) -> None:
    _write_json(path, [segment_to_dict(segment) for segment in segments])


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
    transcription_model: str = "small",
    enable_cache: bool = True,
    progress: Progress | None = None,
) -> dict[str, Path | list[Segment]]:
    ensure_folders(project_dir)
    input_copy = _copy_input(input_video, project_dir)
    output_dir = project_dir / "output"
    temp_dir = project_dir / "temp"
    glossary_path = project_dir / "maritime_glossary.txt"
    log_path = output_dir / "process_log.txt"
    log_path.write_text("DubDeck AI Process Log\n\n", encoding="utf-8")
    progress = _file_progress(progress, log_path)
    demucs_warning = ""

    try:
        _progress(progress, "Checking input video", "Running")
        if input_copy.suffix.lower() != ".mp4":
            raise DubDeckError("No MP4 uploaded. Please upload an .mp4 video.")
        if not has_audio_stream(input_copy):
            raise DubDeckError("Audio detected: no. Please upload a video with an English audio track.")
        _progress(progress, "Checking input video", "Completed")

        _progress(progress, "Extracting audio", "Running", 1, 7, "Extracting speech audio and full-quality original audio.")
        audio_path = temp_dir / "pro_original_audio.wav"
        original_mix_audio = temp_dir / "original_audio_for_mix.wav"
        if not (enable_cache and audio_path.exists()):
            extract_audio(input_copy, audio_path)
        if not (enable_cache and original_mix_audio.exists()):
            extract_audio_for_mixing(input_copy, original_mix_audio)
        _progress(progress, "Extracting audio", "Completed")

        music_path: Path | None = None
        if music_handling == "Use music extracted from input video":
            _progress(progress, "Separating background music", "Running", 2, 7, "Trying to remove English voice and keep music/background.")
            try:
                cached_music = temp_dir / "demucs" / "htdemucs" / audio_path.stem / "no_vocals.wav"
                if enable_cache and cached_music.exists():
                    music_path = cached_music
                else:
                    _vocals, music_path = separate_music_with_demucs(audio_path, temp_dir / "demucs")
                extracted_music = output_dir / "extracted_background_music.wav"
                if music_path and music_path.exists():
                    shutil.copy2(music_path, extracted_music)
                    music_path = extracted_music
                _progress(progress, "Separating background music", "Completed")
            except DubDeckError as exc:
                demucs_warning = (
                    "Music separation failed. You can continue with original audio at reduced volume, upload music, or use no background music."
                )
                _progress(progress, "Separating background music", "Skipped")
                with log_path.open("a", encoding="utf-8") as handle:
                    handle.write(f"{demucs_warning}\nDetails: {exc}\n")

        transcription_json = output_dir / "transcription.json"
        if enable_cache and transcription_json.exists():
            segments = _read_segments_json(transcription_json)
            _progress(progress, "Transcribing English speech", "Completed", 3, 7, "Loaded cached transcription.")
        else:
            _progress(progress, "Transcribing English speech", "Running", 3, 7, f"Using faster-whisper {transcription_model}.")
            segments = transcribe_segments(audio_path, progress, transcription_model)
            _write_segments_json(transcription_json, segments)

        english_srt = output_dir / "english_timed_transcript.srt"
        write_srt(english_srt, segments, language="english")

        translated_json = output_dir / "translated_segments.json"
        if enable_cache and translated_json.exists():
            segments = _read_segments_json(translated_json)
            _progress(progress, "Translating to Hindi", "Completed", 4, 7, "Loaded cached Hindi translations.")
        else:
            _progress(progress, "Translating to Hindi", "Running", 4, 7, "Translating timestamped segments to Hindi.")
            translated = translate_segments_with_glossary([segment.english for segment in segments], glossary_path)
            for segment, hindi in zip(segments, translated):
                segment.hindi = hindi
            _write_segments_json(translated_json, segments)

        hindi_srt = output_dir / "hindi_timed_script.srt"
        write_srt(hindi_srt, segments, language="hindi")
        _progress(progress, "Translating to Hindi", "Completed")
        _progress(progress, "Waiting for Hindi script review", "Running")
        log_message = "Pro Sync preparation completed. Waiting for review.\n"
        if demucs_warning:
            log_message += f"\nMusic note: {demucs_warning}\n"
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(log_message)
        result: dict[str, Path | list[Segment]] = {
            "input_video": input_copy,
            "audio": audio_path,
            "original_mix_audio": original_mix_audio,
            "english_srt": english_srt,
            "hindi_srt": hindi_srt,
            "transcription_json": transcription_json,
            "translated_json": translated_json,
            "segments": segments,
            "log": log_path,
        }
        if music_path:
            result["music"] = music_path
        if demucs_warning:
            result["music_warning"] = demucs_warning
        return result
    except (DubDeckError, TranslationError) as exc:
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(f"Pro Sync failed: {exc}\n")
        raise


def pro_render(
    input_video: Path,
    segments: list[Segment],
    project_dir: Path,
    voice: str,
    music_handling: str,
    background_music_path: Path | None,
    separated_music_path: Path | None,
    original_audio_path: Path | None = None,
    voice_volume: int = 100,
    background_volume: int = 18,
    fallback_volume: int = 12,
    auto_speed_fit: bool = True,
    enable_cache: bool = True,
    parallel_tts: bool = False,
    progress: Progress | None = None,
) -> dict[str, Path]:
    output_dir = project_dir / "output"
    temp_dir = project_dir / "temp"
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / "process_log.txt"
    if not log_path.exists():
        log_path.write_text("DubDeck AI Process Log\n\n", encoding="utf-8")
    progress = _file_progress(progress, log_path)

    try:
        video_len = video_duration(input_video)
        hindi_srt = output_dir / "hindi_timed_script.srt"
        write_srt(hindi_srt, segments, language="hindi")

        _write_segments_json(output_dir / "translated_segments.json", segments)

        _progress(progress, "Generating Hindi voice", "Running", 5, 7, "Generating and fitting Hindi voice by timestamp.")
        final_voice = output_dir / "final_hindi_voice.wav"
        final_voice, updated_segments, manual_fix = place_segments_on_timeline(
            segments,
            video_len,
            voice,
            temp_dir / "tts_segments",
            final_voice,
            auto_speed_fit=auto_speed_fit,
            enable_cache=enable_cache,
            parallel_tts=parallel_tts,
            progress=progress,
        )
        _write_segments_json(output_dir / "translated_segments.json", updated_segments)
        _progress(progress, "Generating Hindi voice", "Completed")

        _progress(progress, "Syncing Hindi voice to video timeline", "Completed")
        needs_manual_fix = output_dir / "needs_manual_fix.txt"
        write_needs_manual_fix(needs_manual_fix, manual_fix)

        _progress(progress, "Mixing background music", "Running", 6, 7, "Mixing background audio under new Hindi voice.")
        music_path = None
        music_volume = background_volume
        if music_handling == "Use music extracted from input video":
            music_path = separated_music_path
            if not music_path and original_audio_path:
                music_path = original_audio_path
                music_volume = fallback_volume
        elif music_handling == "Upload background music":
            music_path = background_music_path
        elif music_handling == "Use original audio at low volume":
            music_path = original_audio_path
            music_volume = fallback_volume
        elif music_handling == "No background music":
            music_path = None
        final_mixed = output_dir / "final_mixed_audio.wav"
        mix_voice_with_music(
            final_voice,
            music_path,
            final_mixed,
            [(segment.start, segment.end) for segment in updated_segments],
            video_len,
            voice_volume=voice_volume,
            background_volume=music_volume,
        )
        _progress(progress, "Mixing background music", "Completed")

        _progress(progress, "Exporting final video", "Running", 7, 7, "Copying original video stream and attaching final mixed audio.")
        output_video = output_dir / "output_hindi.mp4"
        merge_audio_with_video(input_video, final_mixed, output_video)
        _progress(progress, "Exporting final video", "Completed")

        report = output_dir / "sync_report.txt"
        create_sync_report(report, input_video.name, video_len, updated_segments, manual_fix)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write("Pro Sync completed successfully.\n")
        return {
            "output_video": output_video,
            "final_voice": final_voice,
            "final_mixed": final_mixed,
            "hindi_srt": hindi_srt,
            "report": report,
            "needs_manual_fix": needs_manual_fix,
            "log": log_path,
            "process_log": log_path,
            "transcription_json": output_dir / "transcription.json",
            "translated_json": output_dir / "translated_segments.json",
        }
    except Exception as exc:
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(f"Pro Sync export failed: {exc}\n")
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
        background_music_path=background_music_path,
        separated_music_path=prepared.get("music"),  # type: ignore[arg-type]
        original_audio_path=prepared.get("original_mix_audio"),  # type: ignore[arg-type]
        progress=progress,
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
