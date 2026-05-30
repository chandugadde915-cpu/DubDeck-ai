# Operations

## Retry Policy

- Network calls to OpenAI: 3 attempts with exponential backoff.
- FFmpeg steps: 2 attempts, then mark the project as failed.
- TTS segment generation: retry per segment; do not restart completed segments.
- QA: no retranslating; validate existing artifacts only.

## Logging

Use structured logs:

```json
{
  "projectId": "project-id",
  "jobId": "bullmq-job-id",
  "step": "generate-tts",
  "level": "info",
  "message": "Generated segment 12/80"
}
```

## Monitoring

Track:

- Queue depth
- Job duration by step
- OpenAI token/audio usage
- FFmpeg failures
- Render duration
- QA pass rate
- Cost per finished minute

## Cost Controls

- Chunk long audio.
- Cache transcription, translation, TTS, and rendered segment assets.
- Rewrite only long segments.
- Use video stream copy for exports.
- Scale workers based on queue depth.

