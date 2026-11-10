# Kaggle dataset integration for NUIT Guard

Generate a **harmless synthetic audio dataset** with five balanced classes, metadata for Kaggle, and 48 kHz WAV files. The `nuit_like_simulated` label is **not** verified NUIT exploitation. Synthetic audio is used for educational signal-analysis only.

## Run locally (from the `nuit-guard` folder)

```bash
python -m pip install numpy scipy
python dataset_tools/generate_dataset.py --count 1000 --output dataset_tools/kaggle_upload
python dataset_tools/prepare_kaggle.py --folder dataset_tools/kaggle_upload --username YOUR_KAGGLE_USERNAME
```

This produces `metadata.csv`, `DATASET_CARD.md`, `audio_wav.zip`, and `dataset-metadata.json`. A folder `audio/` contains uncompressed original samples. For the Kaggle CLI, its default behavior **skips folders**, so use `--ignore-patterns 'audio/*'` when creating the dataset from this folder to upload the packed ZIP instead of uncompressed audio.

## Publish to Kaggle (account authentication required)

1. Create a Kaggle account and configure a Kaggle API token locally, following Kaggle's latest official instructions. **Never commit your token to GitHub or paste it into a shared notebook.**
2. Install the CLI: `python -m pip install kaggle`
3. From the `nuit-guard` folder, publish privately first:

```bash
kaggle datasets create -p dataset_tools/kaggle_upload --ignore-patterns 'audio/*'
```

If your installed CLI does not support ignore patterns, create a separate upload folder with only `metadata.csv`, `DATASET_CARD.md`, `audio_wav.zip`, and `dataset-metadata.json`, then publish that folder.

To publish publicly, add `--public` when creating, or change visibility on Kaggle.

**Official commands:** https://github.com/Kaggle/kaggle-cli/blob/main/docs/datasets.md

## Use Kaggle data in NUIT Guard

Download your published dataset from Kaggle, extract `audio_wav.zip`, then use the dashboard's WAV upload feature to analyze any sample. The current NUIT Guard app analyzes individual WAV files; it does **not** automatically train a model or fetch every Kaggle sample.

## Repeatability and limits

`--seed` controls deterministic generation. The data has artificial patterns; accuracy measured on this dataset is not evidence of real-world NUIT defense performance. No user speech or third-party files are included.
