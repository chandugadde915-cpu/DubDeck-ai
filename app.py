from __future__ import annotations

import os
import shutil
from pathlib import Path

import streamlit as st

from audio_utils import DubDeckError, check_ffmpeg, ensure_folders, has_audio_stream, video_duration
from dubbing_engine import dry_run_check, pro_prepare, pro_render, quick_prepare, quick_render
from subtitle_utils import Segment, seconds_to_srt_time, segments_to_rows
from translate_utils import TranslationError, install_argos_hint


PROJECT_DIR = Path(__file__).resolve().parent
INPUT_DIR = PROJECT_DIR / "input"
OUTPUT_DIR = PROJECT_DIR / "output"
TEMP_DIR = PROJECT_DIR / "temp"
ASSETS_DIR = PROJECT_DIR / "assets"
CACHE_DIR = TEMP_DIR / "cache"

ensure_folders(PROJECT_DIR)
CACHE_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("TORCH_HOME", str(CACHE_DIR / "torch"))
os.environ.setdefault("XDG_CACHE_HOME", str(CACHE_DIR))
os.environ.setdefault("PYTHONPYCACHEPREFIX", str(CACHE_DIR / "pycache"))

STEPS = [
    "Checking input video",
    "Extracting audio",
    "Separating background music",
    "Transcribing English speech",
    "Translating to Hindi",
    "Waiting for Hindi script review",
    "Generating Hindi voice",
    "Syncing Hindi voice to video timeline",
    "Mixing background music",
    "Exporting final video",
]


def init_state() -> None:
    st.session_state.setdefault("statuses", {step: "Waiting" for step in STEPS})
    st.session_state.setdefault("stage", "home")
    st.session_state.setdefault("mode", "")
    st.session_state.setdefault("input_video", None)
    st.session_state.setdefault("prepared", None)
    st.session_state.setdefault("final_files", None)
    st.session_state.setdefault("error", "")


def set_status(step: str, status: str) -> None:
    st.session_state.statuses[step] = status


def reset_statuses() -> None:
    st.session_state.statuses = {step: "Waiting" for step in STEPS}


def save_uploaded_file(uploaded_file, target_dir: Path) -> Path | None:
    if uploaded_file is None:
        return None
    target = target_dir / "input.mp4"
    with target.open("wb") as handle:
        handle.write(uploaded_file.getbuffer())
    return target


def save_background_music(uploaded_file) -> Path | None:
    if uploaded_file is None:
        return None
    suffix = Path(uploaded_file.name).suffix or ".mp3"
    target = ASSETS_DIR / f"background_music{suffix}"
    with target.open("wb") as handle:
        handle.write(uploaded_file.getbuffer())
    return target


def status_badge(status: str) -> str:
    colors = {
        "Waiting": "#6b7280",
        "Running": "#d97706",
        "Completed": "#15803d",
        "Skipped": "#0f766e",
        "Failed": "#b91c1c",
    }
    return f"<span class='badge' style='background:{colors.get(status, '#64748b')}'>{status}</span>"


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --ink: #102033;
            --muted: #64748b;
            --page: #eef6f8;
            --card: #ffffff;
            --line: #d6e4ea;
            --navy: #102a43;
            --teal: #0f9f96;
            --teal-dark: #0b766f;
            --amber: #f59e0b;
            --coral: #f9735b;
            --soft-blue: #dff3f7;
        }
        .stApp {
            background:
                linear-gradient(180deg, rgba(223, 243, 247, .92) 0%, rgba(238, 246, 248, .96) 42%, #f8fafc 100%);
            color: var(--ink);
        }
        .block-container {
            max-width: 1180px;
            padding-top: 1.6rem;
            padding-bottom: 3rem;
        }
        section[data-testid="stSidebar"] {
            background: #f8fbfc;
            border-right: 1px solid var(--line);
        }
        h1, h2, h3, label, p, span, div {
            letter-spacing: 0;
        }
        .hero {
            position: relative;
            overflow: hidden;
            padding: 30px 32px;
            border: 1px solid rgba(15, 159, 150, .24);
            background:
                linear-gradient(135deg, #12354d 0%, #155e75 52%, #0f766e 100%);
            color: #ffffff;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 18px 44px rgba(16, 42, 67, .18);
        }
        .hero::after {
            content: "";
            position: absolute;
            inset: auto 28px -56px auto;
            width: 210px;
            height: 210px;
            border: 1px solid rgba(255,255,255,.24);
            transform: rotate(18deg);
            border-radius: 8px;
            opacity: .55;
        }
        .hero h1 {
            font-size: 46px;
            line-height: 1.05;
            margin: 0 0 8px 0;
            letter-spacing: 0;
        }
        .hero p {
            font-size: 18px;
            color: #d8f6f3;
            margin: 0;
        }
        .panel, .mode-card, .progress-card {
            background: var(--card);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 12px 30px rgba(16, 42, 67, .10);
        }
        .mode-card {
            min-height: 188px;
            border-top: 5px solid var(--teal);
            transition: transform .16s ease, box-shadow .16s ease, border-color .16s ease;
        }
        .mode-card:hover {
            transform: translateY(-2px);
            border-color: #9bd8d3;
            box-shadow: 0 18px 38px rgba(16, 42, 67, .14);
        }
        .mode-card h3 {
            margin-top: 0;
            color: var(--navy);
            font-size: 24px;
        }
        .muted {
            color: var(--muted);
            line-height: 1.55;
        }
        .badge {
            display: inline-block;
            color: white;
            border-radius: 999px;
            padding: 4px 10px;
            font-size: 12px;
            font-weight: 700;
        }
        .metric-line {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #e7eef2;
            padding: 10px 0;
            gap: 14px;
            color: var(--ink);
        }
        .metric-line:last-child {
            border-bottom: 0;
        }
        div[data-testid="stFileUploader"] section {
            background: #f6fbfc;
            border-color: #b9dce4;
            border-radius: 8px;
        }
        div[data-baseweb="select"] > div {
            border-color: #c7dce3;
            background-color: #ffffff;
        }
        textarea, input {
            border-color: #c7dce3 !important;
            border-radius: 7px !important;
        }
        div[data-testid="stButton"] > button {
            border-radius: 7px;
            font-weight: 700;
            border: 1px solid var(--teal);
            background: var(--teal);
            color: white;
            min-height: 2.8rem;
            box-shadow: 0 8px 18px rgba(15, 159, 150, .20);
        }
        div[data-testid="stButton"] > button:hover {
            border-color: var(--teal-dark);
            background: var(--teal-dark);
            color: white;
        }
        div[data-testid="stDownloadButton"] > button {
            border-radius: 7px;
            font-weight: 700;
            border-color: var(--navy);
            color: var(--navy);
        }
        div[data-testid="stAlert"] {
            border-radius: 8px;
        }
        .stDataFrame, div[data-testid="stDataEditor"] {
            border-radius: 8px;
            overflow: hidden;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def header() -> None:
    st.markdown(
        """
        <div class="hero">
            <h1>DubDeck AI</h1>
            <p>English Training Video to Synced Hindi Voiceover</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def settings_panel() -> dict[str, object]:
    st.markdown("### Studio Settings")
    voice_choice = st.selectbox(
        "Hindi voice",
        ["Male: hi-IN-MadhurNeural", "Female: hi-IN-SwaraNeural"],
    )
    speech_style = st.selectbox("Speech style", ["Natural", "Slow Training Voice", "Sync Optimized"])
    translation_mode = st.selectbox("Translation mode", ["Automatic", "Manual Review Recommended"])
    music_handling = st.selectbox(
        "Music handling",
        ["Keep original background music", "Remove background music", "Add new background music"],
    )
    bg_music = None
    if music_handling == "Add new background music":
        bg_music = st.file_uploader("Upload background music", type=["mp3", "wav", "m4a"], key="bg_music")
    voice = "hi-IN-MadhurNeural" if voice_choice.startswith("Male") else "hi-IN-SwaraNeural"
    return {
        "voice": voice,
        "speech_style": speech_style,
        "translation_mode": translation_mode,
        "music_handling": music_handling,
        "background_music": bg_music,
    }


def upload_panel() -> Path | None:
    st.markdown("### Upload Video")
    uploaded = st.file_uploader("Upload MP4 video", type=["mp4"])
    input_path = save_uploaded_file(uploaded, INPUT_DIR)
    if input_path:
        st.session_state.input_video = str(input_path)
    elif (INPUT_DIR / "input.mp4").exists():
        input_path = INPUT_DIR / "input.mp4"
        st.session_state.input_video = str(input_path)

    if input_path:
        st.markdown(f"**File:** `{input_path.name}`")
        try:
            duration = video_duration(input_path)
            audio = "Yes" if has_audio_stream(input_path) else "No"
            st.markdown(
                f"""
                <div class="metric-line"><span>Duration</span><strong>{seconds_to_srt_time(duration).replace(',', '.')}</strong></div>
                <div class="metric-line"><span>Audio detected</span><strong>{audio}</strong></div>
                """,
                unsafe_allow_html=True,
            )
        except Exception as exc:
            st.warning(f"Video check could not finish: {exc}")
    else:
        st.info("Upload an MP4 or place one at input/input.mp4.")
    return input_path


def progress_panel() -> None:
    st.markdown("### Progress")
    for step in STEPS:
        status = st.session_state.statuses.get(step, "Waiting")
        st.markdown(
            f"<div class='metric-line'><span>{step}</span>{status_badge(status)}</div>",
            unsafe_allow_html=True,
        )


def handle_error(exc: Exception) -> None:
    for step, status in st.session_state.statuses.items():
        if status == "Running":
            st.session_state.statuses[step] = "Failed"
    st.session_state.error = str(exc)
    st.error(str(exc))
    if isinstance(exc, TranslationError):
        st.info(install_argos_hint())


def home_screen() -> None:
    left, right = st.columns([1.35, 1])
    with left:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        input_path = upload_panel()
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        settings = settings_panel()
        st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    card_a, card_b = st.columns(2)
    with card_a:
        st.markdown(
            """
            <div class='mode-card'>
                <h3>Quick Dub Mode</h3>
                <p class='muted'>Fast Hindi dubbing. Best for simple training videos.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Start Quick Dub", use_container_width=True):
            if not input_path:
                st.error("No MP4 uploaded.")
                return
            reset_statuses()
            st.session_state.mode = "quick"
            try:
                prepared = quick_prepare(input_path, PROJECT_DIR, set_status)
                st.session_state.prepared = {key: str(value) for key, value in prepared.items()}
                st.session_state.settings = settings
                st.session_state.stage = "quick_review"
                st.rerun()
            except Exception as exc:
                handle_error(exc)
    with card_b:
        st.markdown(
            """
            <div class='mode-card'>
                <h3>Pro Sync Mode</h3>
                <p class='muted'>Timeline-based Hindi dubbing with music sync. Best for professional training videos.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Start Pro Sync", use_container_width=True):
            if not input_path:
                st.error("No MP4 uploaded.")
                return
            reset_statuses()
            st.session_state.mode = "pro"
            try:
                prepared = pro_prepare(input_path, PROJECT_DIR, settings["music_handling"], set_status)
                st.session_state.prepared = {
                    key: ([segment.__dict__ for segment in value] if key == "segments" else str(value))
                    for key, value in prepared.items()
                }
                st.session_state.settings = settings
                st.session_state.stage = "pro_review"
                st.rerun()
            except Exception as exc:
                handle_error(exc)

    st.write("")
    st.markdown("<div class='progress-card'>", unsafe_allow_html=True)
    progress_panel()
    st.markdown("</div>", unsafe_allow_html=True)


def quick_review_screen() -> None:
    prepared = st.session_state.prepared or {}
    settings = st.session_state.settings
    english_path = Path(prepared["english"])
    hindi_path = Path(prepared["hindi"])

    st.markdown("### Quick Dub Review")
    col1, col2 = st.columns(2)
    with col1:
        st.text_area("English transcript", english_path.read_text(encoding="utf-8"), height=360, disabled=True)
    with col2:
        hindi_text = st.text_area("Editable Hindi script", hindi_path.read_text(encoding="utf-8"), height=360)

    a, b = st.columns(2)
    with a:
        if st.button("Save Hindi Script", use_container_width=True):
            hindi_path.write_text(hindi_text, encoding="utf-8")
            st.success("Hindi script saved.")
    with b:
        if st.button("Continue Voice Generation", use_container_width=True):
            try:
                files = quick_render(
                    Path(prepared["input_video"]),
                    hindi_text,
                    PROJECT_DIR,
                    settings["voice"],
                    settings["speech_style"],
                    set_status,
                )
                st.session_state.final_files = {key: str(value) for key, value in files.items()}
                st.session_state.stage = "final"
                st.rerun()
            except Exception as exc:
                handle_error(exc)
    progress_panel()


def pro_review_screen() -> None:
    prepared = st.session_state.prepared or {}
    settings = st.session_state.settings
    segments = [Segment(**item) for item in prepared["segments"]]

    st.markdown("### Pro Sync Segment Review")
    if prepared.get("music_warning"):
        st.warning(prepared["music_warning"])
    edited = st.data_editor(
        segments_to_rows(segments),
        use_container_width=True,
        height=440,
        disabled=["Segment", "Start", "End", "English text", "Fit status"],
        column_config={"Hindi text": st.column_config.TextColumn(width="large")},
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save Edited Segments", use_container_width=True):
            for index, row in enumerate(edited):
                segments[index].hindi = row["Hindi text"]
            from subtitle_utils import write_srt

            write_srt(OUTPUT_DIR / "hindi_timed_script.srt", segments, language="hindi")
            st.success("Segments saved.")
    with col2:
        if st.button("Continue Sync Export", use_container_width=True):
            try:
                for index, row in enumerate(edited):
                    segments[index].hindi = row["Hindi text"]
                bg_music_path = save_background_music(settings.get("background_music"))
                files = pro_render(
                    Path(prepared["input_video"]),
                    segments,
                    PROJECT_DIR,
                    settings["voice"],
                    settings["music_handling"],
                    bg_music_path,
                    Path(prepared["music"]) if "music" in prepared else None,
                    set_status,
                )
                st.session_state.final_files = {key: str(value) for key, value in files.items()}
                st.session_state.stage = "final"
                st.rerun()
            except Exception as exc:
                handle_error(exc)
    progress_panel()


def file_download(label: str, path: Path, mime: str = "application/octet-stream") -> None:
    if path.exists():
        st.download_button(label, path.read_bytes(), file_name=path.name, mime=mime, use_container_width=True)


def final_screen() -> None:
    files = {key: Path(value) for key, value in (st.session_state.final_files or {}).items()}
    output_video = files.get("output_video")
    st.markdown("### Final Output")
    if output_video and output_video.exists():
        st.video(str(output_video))
        st.success(f"Final MP4 ready: {output_video.name}")

    cols = st.columns(3)
    with cols[0]:
        if output_video:
            file_download("Download final MP4", output_video, "video/mp4")
    with cols[1]:
        archive = OUTPUT_DIR / "dubdeck_outputs.zip"
        if st.button("Prepare transcript ZIP", use_container_width=True):
            if archive.exists():
                archive.unlink()
            shutil.make_archive(str(archive.with_suffix("")), "zip", OUTPUT_DIR)
        file_download("Download transcripts", archive, "application/zip")
    with cols[2]:
        report = files.get("report") or OUTPUT_DIR / "quick_dub_log.txt"
        file_download("Download sync report", report, "text/plain")

    if st.button("Start new project", use_container_width=True):
        st.session_state.stage = "home"
        st.session_state.prepared = None
        st.session_state.final_files = None
        reset_statuses()
        st.rerun()

    progress_panel()


def sidebar_health() -> None:
    with st.sidebar:
        st.markdown("## DubDeck Health")
        st.write("FFmpeg:", "Ready" if check_ffmpeg() else "Missing")
        if st.button("Run dry check"):
            for line in dry_run_check(PROJECT_DIR):
                st.write(line)
        st.caption("Processing runs on this laptop using free local tools.")


def main() -> None:
    st.set_page_config(page_title="DubDeck AI", page_icon="DD", layout="wide")
    init_state()
    inject_css()
    header()
    sidebar_health()

    if st.session_state.error:
        st.warning(st.session_state.error)

    if st.session_state.stage == "quick_review":
        quick_review_screen()
    elif st.session_state.stage == "pro_review":
        pro_review_screen()
    elif st.session_state.stage == "final":
        final_screen()
    else:
        home_screen()


if __name__ == "__main__":
    main()
