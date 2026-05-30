# Deploy DubDeck AI

DubDeck AI has two parts:

1. The local Streamlit video processor in the project root.
2. The Vercel-ready public landing page in `vercel_landing/`.

The repository root now includes a Vercel-safe `index.html`, so Vercel can deploy the project even if you leave **Root Directory** as the repository root.

Keep the Streamlit video processor local because it uses FFmpeg, faster-whisper, Demucs, and long-running laptop processing.

## Push To GitHub

Create a new empty GitHub repository, then run these commands from this folder:

```bash
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git branch -M main
git push -u origin main
```

If the remote already exists:

```bash
git remote set-url origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

## Deploy Landing Page To Vercel

Recommended Vercel dashboard steps:

1. Go to Vercel.
2. Import the GitHub repository.
3. Leave **Root Directory** as the repository root, or set it to `vercel_landing`.
4. Leave framework preset as **Other**.
5. Deploy.

## Deploy With Vercel CLI

If Vercel CLI is installed and logged in:

```bash
cd vercel_landing
vercel
vercel --prod
```

## Important

Do not deploy the full Streamlit processor as a normal Vercel serverless app. It needs local files, model caches, FFmpeg, and long-running CPU work.
