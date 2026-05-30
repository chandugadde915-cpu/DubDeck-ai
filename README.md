# DubDeck AI

**English Training Video to Synced Hindi Voiceover**

DubDeck AI is a local Streamlit product that converts English MP4 training videos into Hindi voiceover MP4 videos using free tools only.

It is designed for training content creators, maritime trainers, ship staff training teams, and safety training teams.

## What It Does

1. Upload an English MP4 training video.
2. Transcribe the English speech with faster-whisper.
3. Translate English text to Hindi with Argos Translate.
4. Protect maritime terms like vessel, SIRE, PSC, SOLAS, MARPOL, and permit to work.
5. Generate Hindi speech with edge-tts.
6. Export a Hindi voiceover MP4.

## Quick Dub Mode vs Pro Sync Mode

**Quick Dub Mode** creates one full Hindi voiceover. It is fastest and works well when exact timing is not important.

**Pro Sync Mode** creates Hindi voice segment by segment, places speech on the original timeline, mixes background music, and creates a sync report.

## Mac Installation

1. Install Python from <https://www.python.org/downloads/>.
2. Install Homebrew if you do not already have it: <https://brew.sh/>.
3. Install FFmpeg:

```bash
brew install ffmpeg
```

4. Open Terminal in this folder.
5. Run:

```bash
chmod +x run_mac.command
./run_mac.command
```

## Windows Installation

1. Install Python from <https://www.python.org/downloads/windows/>.
2. During installation, tick **Add Python to PATH**.
3. Install FFmpeg and add it to PATH.
4. Double-click `run_windows.bat`.

## Install FFmpeg

Mac:

```bash
brew install ffmpeg
ffmpeg -version
```

Windows:

1. Download FFmpeg from <https://ffmpeg.org/download.html>.
2. Extract it.
3. Add the `bin` folder to your Windows PATH.
4. Open Command Prompt and run:

```bat
ffmpeg -version
```

## Install Argos English-to-Hindi Translation

DubDeck AI uses Argos Translate, not paid translation APIs.

If the app says the English-to-Hindi package is missing, install the Argos package in Python. One beginner-friendly way is:

```bash
python -m pip install argostranslate
```

Then install the English-to-Hindi package from Argos Translate packages. After that, restart DubDeck AI.

## How To Run

Mac:

```bash
./run_mac.command
```

Windows:

```bat
run_windows.bat
```

The app opens in your browser, usually at:

```text
http://localhost:8501
```

## How To Upload Video

Use the upload button in the app, or place a file named `input.mp4` inside:

```text
input/
```

## How To Review Hindi Script

Quick Dub Mode shows:

- English transcript
- Editable Hindi script

Pro Sync Mode shows:

- Segment number
- Start time
- End time
- English text
- Editable Hindi text
- Fit status

Edit the Hindi text before continuing to voice generation.

## Where Output Files Are Saved

All exported files appear in:

```text
output/
```

Quick Dub files:

- `english_transcript.txt`
- `hindi_voiceover_script_for_tts.txt`
- `hindi_voiceover_single.mp3`
- `output_hindi_quick.mp4`
- `quick_dub_log.txt`

Pro Sync files:

- `english_timed_transcript.srt`
- `hindi_timed_script.srt`
- `final_hindi_voice.wav`
- `final_mixed_audio.wav`
- `output_hindi_synced.mp4`
- `sync_report.txt`
- `needs_manual_fix.txt`
- `pro_sync_log.txt`

## How To Change Hindi Voice

Use the Hindi voice setting:

- Male: `hi-IN-MadhurNeural`
- Female: `hi-IN-SwaraNeural`

## How To Add Background Music

Choose **Add new background music** in the settings panel, then upload an MP3, WAV, or M4A file.

For Pro Sync Mode, DubDeck AI ducks the background music while Hindi voice is speaking.

## Maritime Glossary

The file `maritime_glossary.txt` protects key maritime terms from poor translation.

You can add your own terms, one per line.

## Common Errors and Solutions

**FFmpeg error appears**

Run:

```bash
ffmpeg -version
```

If that fails, install FFmpeg and add it to PATH.

**Python command fails on Mac**

Use:

```bash
python3
```

**Python command fails on Windows**

Use:

```bat
py
```

**Argos English-Hindi package missing**

Install the English-to-Hindi package for Argos Translate, then restart the app.

**Hindi voice is too fast**

Choose **Slow Training Voice**.

**Translation is wrong**

Edit the Hindi script before export.

**Pro Sync Mode has manual fix lines**

Shorten those Hindi lines and run export again.

**Demucs music separation failed**

Choose **Remove background music** or upload new background music.

## Vercel Hosting Note

DubDeck AI is built as a local laptop app. Full video processing is not suitable for a normal Vercel deployment because it needs FFmpeg, Demucs, Whisper model files, local disk work, and long-running CPU jobs.

Recommended setup:

- Run the full DubDeck AI processor locally with Streamlit.
- Use Vercel only for a public landing page, documentation, or a lightweight demo that tells users how to download and run the local app.

This project includes a Vercel-ready static landing page in:

```text
vercel_landing/
```

Deploy that folder to Vercel. Keep the main Streamlit processor local.

To make the real processing cloud-hosted later, use a dedicated worker machine or container service with FFmpeg, model storage, and long job timeouts.

## AWS EC2 Full Product Hosting

To host the full product on AWS using local server folders only, use the Docker-based EC2 guide:

```text
AWS_EC2_DEPLOYMENT.md
```

AWS package details are listed in:

```text
AWS_PACKAGES.md
```

This keeps uploaded videos, temporary files, caches, and output MP4 files in the EC2 project folders. It does not use S3.
