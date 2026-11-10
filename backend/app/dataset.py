"""Read a locally cached Kaggle dataset. No secret credentials reach the browser."""
from pathlib import Path
import os
import csv

ROOT = Path(os.environ.get("NUIT_DATA_DIR", str(Path(__file__).resolve().parent.parent / "data")))

def wav_files():
    if not ROOT.exists():
        return []
    return sorted((f for f in ROOT.rglob('*.wav') if f.is_file()), key=lambda f: f.name)

def samples(limit=50):
    rows = {}
    for metadata in ROOT.rglob('metadata.csv') if ROOT.exists() else []:
        try:
            with metadata.open(newline='', encoding='utf-8') as fh:
                for row in csv.DictReader(fh):
                    key = Path(row.get('filename', row.get('file_name', ''))).name
                    if key: rows[key] = row
        except (OSError, UnicodeError):
            pass
    return [{"filename": f.name, "category": rows.get(f.name, {}).get('category') or rows.get(f.name, {}).get('label') or 'unlabeled', "bytes": f.stat().st_size} for f in wav_files()[:limit]]

def find_sample(filename):
    if filename != Path(filename).name or not filename.lower().endswith('.wav'):
        return None
    return next((f for f in wav_files() if f.name == filename), None)
