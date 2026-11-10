# NUIT Guard — Educational Audio Threat Analysis Platform

A full-stack student project inspired by **Qi Xia, Qian Chen, and Shouhuai Xu, “Near-Ultrasound Inaudible Trojan (NUIT): Exploiting Your Speaker to Attack Your Microphone,” USENIX Security 2023**.

**This is not a reproduction of the attack or a validated security product.** It is a learning-oriented audio analyzer implementing a **research-inspired high-band/baseband cross-correlation heuristic**, with an interactive React dashboard and safe, non-voice simulated test signals.

## Requirements
- Python 3.10+
- Node.js 18+ and npm
- 44.1 kHz or 48 kHz WAV/FLAC samples (recommended: 48 kHz PCM WAV)

## Quick start

**Terminal 1 — backend**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate       # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Terminal 2 — frontend**
```bash
cd frontend
npm install
npm run dev
```
Open **http://127.0.0.1:5173**. FastAPI interactive docs: **http://127.0.0.1:8000/docs**.

## Testing
```bash
cd backend
pytest -q
```
Frontend production build:
```bash
cd frontend
npm run build
```

## Features
- Local upload to a stateless API; file contents are read in memory and not saved to a database
- Validated WAV/FLAC decoding, duration and upload-size limits, sample rate restrictions
- Low-band (100–6000 Hz) and near-ultrasound (16–22 kHz) analysis
- FFT-based bounded-lag normalized cross-correlation comparing baseband audio with nonlinear high-band envelope estimates
- Signal waveform, power spectrum, and per-window correlation plots
- Adjustable sensitivity threshold and downloadable JSON results
- Three controlled demonstration audio samples with **no voice commands or exploit payloads**
- Automated API and input-validation tests

## API
- `GET /api/health`
- `POST /api/analyze?threshold=0.55` — multipart upload field `file`
- `GET /api/demo/normal`
- `GET /api/demo/harmless_high`
- `GET /api/demo/simulated_nonlinear`

## Interpretation and limitations
A positive finding means the heuristic observed *both* high-band energy and correlation with a lower-frequency component. Correlation is **not proof of malicious intent or NUIT execution**. A negative finding **does not certify safety**. Threshold 0.55 is a configurable educational default; it is **not clinically/statistically calibrated**.

Real consumer microphones, speakers, lossy audio formats, compression, varying sample rates, acoustic reflections, AGC, and low-pass filters can dramatically alter or eliminate near-ultrasound content. The synthetic nonlinear sample models an idealized square-law response and uses harmless sine tones, not genuine speech or an actual voice assistant. The research paper's reported 0 FP/0 FN in a limited simulation **must not** be assumed to generalize to this application.

For a student evaluation, record precision, recall, false-positive rate, time per file and robustness across multiple separately labeled benign recordings. See `docs/PROJECT_REPORT.md` for scope and viva topics.

## Structure
```text
nuit-guard/
├── backend/
│   ├── app/{main.py,detection.py}
│   ├── tests/test_api.py
│   ├── requirements.txt
│   └── requirements-dev.txt
├── frontend/
│   ├── src/{main.jsx,styles.css}
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── docs/PROJECT_REPORT.md
└── README.md
```

## Attribution
Based on conceptual ideas in Section 8 of https://www.usenix.org/conference/usenixsecurity23/presentation/xia . This is an independent educational implementation; not endorsed by the authors.

## Optional: generate a Kaggle synthetic audio dataset

See [`dataset_tools/README.md`](dataset_tools/README.md) for reproducible WAV generation, metadata, Kaggle publishing, and data limitations. This is a synthetic educational benchmark rather than a dataset of real NUIT exploits.
