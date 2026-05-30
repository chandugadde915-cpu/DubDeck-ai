# Architecture

## High-Level System

```text
Browser
  -> Next.js dashboard
  -> NestJS API
  -> PostgreSQL for project data
  -> Redis/BullMQ for workflow jobs
  -> Worker service with FFmpeg + OpenAI APIs
  -> S3/R2 object storage for video/audio/subtitle/report assets
```

## Services

- Upload Service: presigned uploads, asset validation, storage metadata.
- Transcript Service: FFmpeg audio extraction and OpenAI transcription.
- Translation Service: target-language translation with glossary and JSON segment schema.
- Duration Optimization Service: timing analysis and selective rewrite for long segments.
- TTS Service: per-segment target-language audio generation.
- Sync Service: segment audio fitting, silence padding, stitching.
- QA Service: validates timing, missing segments, clipped audio, gaps, placeholders, render failures.
- Export Service: FFmpeg final MP4 render using video stream copy where possible.
- Notification Service: project status updates and email/webhook hooks.
- User Management: auth, organizations, roles.
- Billing: usage tracking, plans, invoices.
- Analytics: throughput, cost, job timing, failure rates.

## Queue Pipeline

One top-level `dub-job` queue orchestrates step jobs:

```text
uploaded
  -> extract-audio
  -> transcribe
  -> translate
  -> duration-fit
  -> rewrite-long-segments
  -> generate-tts
  -> sync-audio
  -> qa
  -> export-video
  -> completed
```

Each step writes idempotent state to PostgreSQL and stores artifacts in S3/R2. A failed step can retry without repeating completed prior steps.

## Scaling

- Run API horizontally behind a load balancer.
- Run workers separately and scale by queue depth.
- Split worker queues later by cost profile:
  - `transcription`
  - `translation`
  - `tts`
  - `ffmpeg`
  - `qa`
- Use Redis job lock durations longer than expected FFmpeg/TTS tasks.
- Use PostgreSQL row status as source of truth, not in-memory state.

