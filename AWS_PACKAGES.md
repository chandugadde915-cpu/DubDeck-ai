# AWS Package Manifest

DubDeck AI installs packages from GitHub using the files in this repository. Do not upload installed `site-packages`, `.venv`, or Docker image layers to GitHub.

## Docker Python Packages

Docker uses:

```text
requirements-docker.txt
```

Packages:

```text
streamlit
numpy<2
faster-whisper
edge-tts
argostranslate
pydub
moviepy
demucs
```

Torch is installed separately in the Dockerfile as CPU-only:

```text
torch==2.2.2+cpu
torchaudio==2.2.2+cpu
```

This avoids large GPU packages and avoids the NumPy 2 compatibility warning.

## Local Mac/Windows Python Packages

Local desktop runs use:

```text
requirements.txt
```

This includes:

```text
audioop-lts
```

`audioop-lts` is needed for Python 3.13+ / 3.14 local runs. Docker uses Python 3.11, so Docker does not install `audioop-lts`.

## System Packages In Docker

The Dockerfile installs:

```text
build-essential
curl
ffmpeg
git
libgomp1
libsndfile1
```

## Argos English-to-Hindi Package

The Docker image installs the free Argos English-to-Hindi package using:

```text
scripts/install_argos_en_hi.py
```

Argos package data is stored locally on EC2:

```text
temp/cache/data/
```

## EC2 Install / Rebuild Commands

From the EC2 project folder:

```bash
git pull
docker compose down
docker compose build --no-cache
docker compose up -d
docker ps
```

Or use:

```bash
bash scripts/ec2_rebuild.sh
```
