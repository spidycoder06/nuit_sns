"""Create the Kaggle dataset metadata and a single archive of WAV files."""
import argparse
import json
from pathlib import Path
import zipfile


def prepare(folder, username, slug='nuit-guard-synthetic-audio'):
    folder = Path(folder)
    if not (folder / 'metadata.csv').is_file() or not (folder / 'audio').is_dir():
        raise ValueError('Generate the dataset first; metadata.csv and audio/ are required')
    username = username.strip()
    if not username or '/' in username or ' ' in username:
        raise ValueError('Provide your Kaggle username, e.g. --username your_kaggle_username')
    archive = folder / 'audio_wav.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted((folder / 'audio').glob('*.wav')):
            z.write(p, p.relative_to(folder))
    meta = {'title': 'NUIT Guard Synthetic Audio Signals',
            'id': f'{username}/{slug}',
            'licenses': [{'name': 'CC0-1.0'}],
            'description': 'Five-category synthetic audio benchmark. Not real NUIT attacks; includes no voice-command payloads.'}
    (folder / 'dataset-metadata.json').write_text(json.dumps(meta, indent=2))
    print(f'Kaggle package prepared: {folder} with {archive.name}, metadata.csv and dataset-metadata.json')
    print('Upload folder files using Kaggle CLI or Kaggle web interface. Do not publish secret keys.')
    return meta


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--folder', default='dataset_tools/kaggle_upload')
    parser.add_argument('--username', required=True)
    args = parser.parse_args()
    prepare(args.folder, args.username)
