# DubDeck AI SaaS Platform

Production-grade AI video dubbing SaaS blueprint and starter monorepo.

This is a separate SaaS architecture track from the local Streamlit tool in the repository root.

## Stack

- Next.js 15
- TypeScript
- Tailwind CSS
- ShadCN UI
- NestJS
- PostgreSQL
- Redis
- BullMQ
- FFmpeg
- OpenAI APIs
- AWS S3 or Cloudflare R2-compatible object storage

## Workflow

```text
Upload Video
  -> Extract Audio
  -> Generate Transcript
  -> Translate to Selected Language
  -> Duration Fit Check
  -> Rewrite Long Segments
  -> Generate TTS Audio
  -> Sync Audio to Video
  -> Automated QA Validation
  -> Export Final Video
```

## Apps

```text
apps/web      Next.js dashboard
apps/api      NestJS HTTP API
apps/worker   BullMQ media-processing worker
packages/db   Prisma schema
packages/shared Shared types
```

## Local Development

```bash
cp .env.example .env
docker compose up -d postgres redis minio
npm install
npm run db:generate
npm run db:migrate
npm run dev
```

## Production Notes

For production, run web, api, and worker as separate deployables. Keep FFmpeg and worker workloads outside serverless request handlers. Store media in S3/R2 and store project/job state in PostgreSQL.

## References

- `docs/ARCHITECTURE.md`
- `docs/PIPELINE.md`
- `docs/API.md`
- `docs/OPERATIONS.md`
