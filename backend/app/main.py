from __future__ import annotations
import os
from .dataset import samples, find_sample, wav_files
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from .detection import AudioValidationError, MAX_FILE_BYTES, analyze, load_audio, make_demo

app = FastAPI(title="NUIT Guard", version="1.0.0", description="Educational near-ultrasound security analysis")
app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in ("http://localhost:5173,http://127.0.0.1:5173," + os.getenv("CORS_ORIGINS", "")).split(",") if x.strip()], allow_methods=["GET", "POST"], allow_headers=["*"])

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "NUIT Guard"}

@app.post("/api/analyze")
async def analyze_upload(file: UploadFile = File(...), threshold: float = Query(0.55, gt=0, lt=1)):
    try:
        data = await file.read(MAX_FILE_BYTES + 1)
        audio, rate = load_audio(data)
        result = analyze(audio, rate, threshold)
        result["filename"] = (file.filename or "audio")[:120]
        return result
    except AudioValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@app.get("/api/demo/{kind}")
def demo(kind: str):
    try:
        result = make_demo(kind)
    except AudioValidationError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(result, media_type="audio/wav", headers={"Content-Disposition": f'attachment; filename="{kind}.wav"'})

@app.get("/api/dataset/status")
def dataset_status():
    return {"configured": bool(os.getenv("KAGGLE_DATASET")), "sample_count": len(wav_files()), "dataset": os.getenv("KAGGLE_DATASET", "not configured")}

@app.get("/api/dataset/samples")
def dataset_samples(limit: int = Query(25, ge=1, le=100)):
    return {"items": samples(limit), "total": len(wav_files())}

@app.get("/api/dataset/analyze/{filename}")
def analyze_dataset(filename: str, threshold: float = Query(0.55, gt=0, lt=1)):
    path = find_sample(filename)
    if path is None:
        raise HTTPException(status_code=404, detail="Dataset audio not found")
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            raise AudioValidationError("Sample exceeds size limit")
        audio, rate = load_audio(path.read_bytes())
        result = analyze(audio, rate, threshold)
        result["filename"] = filename
        return result
    except AudioValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
