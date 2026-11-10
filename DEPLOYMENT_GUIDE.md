# NUIT Guard: Kaggle + Railway + Vercel

## What this integration does
The Railway backend fetches a Kaggle dataset into a temporary local cache on startup (when enabled), exposes a read-only listing of up to 100 WAV samples, and runs the existing signal-analysis algorithm on a selected sample. The React site deployed on Vercel talks to Railway using `VITE_API_URL`. Do not store Kaggle secrets in React/Vercel.

**Prerequisites:** Put your dataset on Kaggle. If you uploaded WAVs only, the explorer will say `unlabeled` because a `metadata.csv` was not provided. Upload the generator's `metadata.csv` as a new Kaggle dataset version for labels. The ZIP format `audio_wav.zip` is also recognized.

### 1. Set up the repository
Unzip project, enter `nuit-guard`, initialize Git, commit and push to your GitHub repository. Do not commit credentials or the `backend/data/` folder.

### 2. Railway backend
Create a Railway project from your GitHub repo, set **Root Directory** `/backend`.
Set **Start Command** to `sh start.sh` (this listens on `$PORT`). Set the following Railway **Variables**:
- `KAGGLE_DATASET`: your-username/your-dataset-slug
- `KAGGLE_SYNC_ON_START`: `1`
- `CORS_ORIGINS`: `https://your-vercel-project.vercel.app`
- If private dataset: `KAGGLE_USERNAME` and `KAGGLE_KEY` (from Kaggle settings, never commit them)

Generate a public Railway domain and check `https://YOUR-RAILWAY-DOMAIN/api/health` and `/api/dataset/status`. If Kaggle sync fails, check deployment logs; the API starts but dataset explorer will be empty. Restarting may fetch the data again since platform disks are ephemeral. For large datasets use object storage or a persistent volume instead of startup downloading.

### 3. Vercel frontend
Import the same GitHub repository into Vercel. **Root Directory** `frontend`; framework **Vite**; Build Command `npm run build`; Output Directory `dist`. Set a Vercel environment variable `VITE_API_URL=https://YOUR-RAILWAY-DOMAIN` (no trailing slash, no /api). Redeploy after setting it. `VITE_API_URL` is public and must never be a secret.

### 4. Test flow
Open the Vercel site → **Load Kaggle samples** → select sample → inspect spectrum, waveform and correlation score. Upload your own WAV and test the demo signals as well. If CORS fails, ensure the exact Vercel URL is in `CORS_ORIGINS`, then redeploy Railway. When using a Vercel preview URL, add that origin explicitly or use your stable production domain.

### Local development
Backend: `cd backend && pip install -r requirements-dev.txt && uvicorn app.main:app --reload`
Frontend: `cd frontend && npm install && npm run dev` (Vite proxy handles /api locally).
Local Kaggle sync: `cd backend && KAGGLE_DATASET=YOUR_USERNAME/YOUR_SLUG python sync_kaggle.py` (private datasets need authenticated Kaggle credentials).

### Limitations and safety
Dataset files are synthetic educational samples, **not validated attack recordings**. Correlation-based detection is a research-inspired heuristic, not guaranteed real-world protection. This backend has no user accounts or rate limiting; avoid exposing it widely with untrusted traffic until you add authentication, rate limits and quotas. The `/api/dataset/analyze/{filename}` endpoint analyzes server-cached filenames only, not arbitrary filesystem paths.
