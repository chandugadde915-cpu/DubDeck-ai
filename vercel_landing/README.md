# DubDeck AI Vercel Landing Page

This folder is safe to deploy to Vercel as a public landing page.

The full Streamlit processor should run locally because Vercel serverless functions are not a good fit for long video jobs, FFmpeg processing, Demucs, Whisper model storage, and local MP4 exports.

## Deploy

From this folder:

```bash
npm install -g vercel
vercel
vercel --prod
```

Or import this folder as a Vercel project through the Vercel dashboard.
