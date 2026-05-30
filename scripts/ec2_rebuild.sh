#!/usr/bin/env bash
set -euo pipefail

echo "Updating DubDeck AI from GitHub..."
git pull

echo "Ensuring local folders exist..."
mkdir -p input output temp assets temp/cache temp/cache/data temp/cache/torch temp/cache/huggingface

echo "Stopping old container if running..."
docker compose down

echo "Building Docker image..."
docker compose build --no-cache

echo "Starting DubDeck AI..."
docker compose up -d

echo "Container status:"
docker ps

echo
echo "DubDeck AI should be available on:"
echo "http://YOUR_EC2_PUBLIC_IP:8501"
