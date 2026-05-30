# DubDeck AI AWS EC2 Deployment

This guide runs the full DubDeck AI product on an AWS EC2 server using local folders only.

No S3. No Lambda. No paid speech or translation APIs.

## Architecture

```text
User browser
  -> EC2 public IP or domain
  -> Docker container running Streamlit
  -> local EC2 project folders
     - input/
     - output/
     - temp/
     - assets/
```

The uploaded videos, temporary files, model caches, and final MP4 files stay on the EC2 server disk.

## Recommended EC2 Server

For testing:

```text
t3.large or t3.xlarge
```

For better video processing:

```text
c6i.xlarge, c7i.xlarge, or larger
```

Storage:

```text
80-150 GB EBS volume
```

Use Ubuntu 22.04 LTS or Ubuntu 24.04 LTS.

## Security Group

For a simple MVP, open:

```text
SSH:       TCP 22    from your IP only
Streamlit: TCP 8501  from your IP or 0.0.0.0/0 for public testing
```

For production, put Nginx and HTTPS in front later instead of exposing port 8501 directly.

## Install Docker On EC2

SSH into your EC2 server:

```bash
ssh -i your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

Update Ubuntu:

```bash
sudo apt update
sudo apt upgrade -y
```

Install Docker:

```bash
sudo apt install -y ca-certificates curl gnupg git
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Allow your Ubuntu user to run Docker:

```bash
sudo usermod -aG docker ubuntu
newgrp docker
```

Check Docker:

```bash
docker --version
docker compose version
```

## Clone DubDeck AI

```bash
git clone https://github.com/chandugadde915-cpu/DubDeck-ai.git
cd DubDeck-ai
```

## Create Local Folders

These folders are bind-mounted into the container and persist on the EC2 disk:

```bash
mkdir -p input output temp assets
```

## Start DubDeck AI

Build and start:

```bash
docker compose up -d --build
```

Open the app:

```text
http://YOUR_EC2_PUBLIC_IP:8501
```

The app allows uploads up to 2 GB by default. You can change this in:

```text
.streamlit/config.toml
```

## Where Files Are Stored

Uploaded video:

```text
input/input.mp4
```

Temporary processing files:

```text
temp/
```

Model and tool caches:

```text
temp/cache/
temp/cache/torch/
temp/cache/huggingface/
```

Final outputs:

```text
output/
```

Example outputs:

```text
output/output_hindi_quick.mp4
output/output_hindi_synced.mp4
output/english_transcript.txt
output/hindi_timed_script.srt
output/sync_report.txt
```

## View Logs

```bash
docker compose logs -f
```

## Restart The App

```bash
docker compose restart
```

## Stop The App

```bash
docker compose down
```

This does not delete your local `input/`, `output/`, `temp/`, or `assets/` folders.

## Update Code From GitHub

```bash
git pull
docker compose up -d --build
```

## Common Problems

### App does not open

Check that the EC2 security group allows TCP port `8501`.

Check logs:

```bash
docker compose logs -f
```

### FFmpeg error

FFmpeg is installed inside the Docker image. Rebuild the container:

```bash
docker compose up -d --build
```

### Demucs downloads model slowly

The first Pro Sync run may download Demucs and model files. These are cached in:

```text
temp/cache/
```

Future runs should be faster as long as you keep the `temp/` folder.

### Disk fills up

Video processing creates large WAV and MP4 files. Delete old files from:

```text
input/
output/
temp/
```

Keep `temp/cache/` if you do not want models to download again.

## Optional Production Setup

Later, you can improve the setup with:

- Nginx reverse proxy
- A domain name
- HTTPS certificate
- Basic password protection
- Regular EBS snapshots
- CloudWatch logs

If you are not using S3, take EBS snapshots or manual backups. Your output files live only on the EC2 disk.
