"""Cache a Kaggle dataset into backend/data for use by the public API.
Run on deploy when KAGGLE_SYNC_ON_START=1, or manually before deployment.
"""
import os
from pathlib import Path
import shutil
import zipfile

slug = os.getenv('KAGGLE_DATASET', '').strip()
if not slug or len(slug.split('/')) != 2:
    raise SystemExit('Set KAGGLE_DATASET=username/dataset-slug')
import kagglehub
source = Path(kagglehub.dataset_download(slug))
dest = Path(os.getenv('NUIT_DATA_DIR', str(Path(__file__).resolve().parent / 'data')))
dest.mkdir(parents=True, exist_ok=True)
count = 0
for f in source.rglob('*'):
    if not f.is_file():
        continue
    if f.suffix.lower() == '.wav':
        shutil.copyfile(f, dest / f.name)
        count += 1
    elif f.name == 'metadata.csv':
        shutil.copyfile(f, dest / f.name)
    elif f.name == 'audio_wav.zip':
        with zipfile.ZipFile(f) as z:
            for item in z.infolist():
                if not item.filename.lower().endswith('.wav') or item.is_dir():
                    continue
                # Ignore nested paths, oversized and duplicate entries.
                name = Path(item.filename).name
                if item.file_size > 20 * 1024 * 1024 or not name:
                    continue
                with z.open(item) as reader, (dest / name).open('wb') as writer:
                    shutil.copyfileobj(reader, writer)
                count += 1
print(f'Cached {count} WAV samples at {dest}')
