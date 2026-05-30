# API Endpoints

## Projects

```text
GET    /projects
POST   /projects
GET    /projects/:id
POST   /projects/:id/process
PATCH  /projects/:id/settings
```

## Uploads

```text
POST /uploads/presign
POST /uploads/complete
```

## Transcript

```text
GET   /projects/:id/segments
PATCH /projects/:id/segments/:segmentId
POST  /projects/:id/segments/bulk-update
```

## Assets

```text
GET /projects/:id/assets
GET /projects/:id/download/final-video
GET /projects/:id/download/srt
GET /projects/:id/download/vtt
GET /projects/:id/download/qa-report
```

## Progress

```text
GET /projects/:id/events
```

Use Server-Sent Events for project progress updates in the dashboard. WebSockets can be added later for collaborative editing.

