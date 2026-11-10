"""Reproducible, harmless, synthetic near-ultrasound dataset for NUIT Guard.

All signals are synthesized; no intelligible commands or attack payloads.
"""
import argparse
import csv
import json
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt, hilbert, resample_poly

RATE = 48000
LABELS = ('speech_like', 'background_noise', 'high_frequency', 'mixed', 'nuit_like_simulated')


def band_energy(signal, lo, hi, rate=RATE):
    f = np.fft.rfftfreq(len(signal), 1 / rate)
    p = np.abs(np.fft.rfft(signal)) ** 2
    idx = (f >= lo) & (f < hi)
    return float(p[idx].sum() / max(p.sum(), 1e-12))


def features(signal, rate=RATE):
    f = np.fft.rfftfreq(len(signal), 1 / rate)
    amps = np.abs(np.fft.rfft(signal))
    return {
        'rms': round(float(np.sqrt(np.mean(signal**2))), 6),
        'peak_frequency_hz': round(float(f[np.argmax(amps)]), 2),
        'energy_0_8khz': round(band_energy(signal, 0, 8000, rate), 6),
        'energy_16_22khz': round(band_energy(signal, 16000, 22000, rate), 6),
    }


def smooth_random(rng, t, low=200, high=2600):
    frequencies = rng.uniform(low, high, size=5)
    phases = rng.uniform(0, 2 * np.pi, size=5)
    amplitudes = rng.uniform(.2, 1, size=5)
    s = sum(a * np.sin(2 * np.pi * f * t + p) for a, f, p in zip(amplitudes, frequencies, phases))
    s = np.asarray(s, dtype=np.float64)
    s /= max(np.max(np.abs(s)), .001)
    envelope = 0.3 + 0.7 * np.sin(np.pi * np.linspace(0, 1, len(t))) ** 2
    return s * envelope


def make_sample(label, seed, duration=1.0, rate=RATE):
    rng = np.random.default_rng(seed)
    n = int(duration * rate)
    t = np.arange(n) / rate
    voice = smooth_random(rng, t)
    f = rng.uniform(16600, 21000)
    carrier = np.sin(2 * np.pi * f * t + rng.uniform(-np.pi, np.pi))
    noise = rng.normal(0, 1, n)
    if label == 'speech_like':
        x = voice + .015 * noise
    elif label == 'background_noise':
        sos = butter(4, rng.uniform(900, 5000), fs=rate, output='sos')
        x = sosfilt(sos, noise)
    elif label == 'high_frequency':
        x = carrier + .008 * noise
    elif label == 'mixed':
        x = .55 * voice + .4 * carrier + .015 * noise
    elif label == 'nuit_like_simulated':
        # Artificial acoustic coupling signature, NOT a functional NUIT injection:
        # nonlinear processing creates a correlated low-frequency shadow.
        modulation = 1 + .35 * voice
        high = modulation * carrier
        low_shadow = high ** 2
        sos = butter(4, 5000, fs=rate, output='sos')
        low_shadow = sosfilt(sos, low_shadow - np.mean(low_shadow))
        x = .8 * high + .75 * low_shadow + .01 * noise
    else:
        raise ValueError(label)
    x = x - np.mean(x)
    x /= max(np.max(np.abs(x)), .0001)
    x *= rng.uniform(.3, .8)
    return np.asarray(x, dtype=np.float32)


def generate(out, count=1000, seed=2026, duration=1.0):
    out = Path(out)
    if count < 5 or count % len(LABELS):
        raise ValueError('count must be a multiple of 5 and at least 5')
    if not .2 <= duration <= 5:
        raise ValueError('duration must be between 0.2 and 5 seconds')
    (out / 'audio').mkdir(parents=True, exist_ok=True)
    rows = []
    for label_idx, label in enumerate(LABELS):
        for j in range(count // len(LABELS)):
            index = label_idx * (count // len(LABELS)) + j
            item_seed = seed + index * 7919
            audio = make_sample(label, item_seed, duration)
            name = f'{label}_{j:04d}.wav'
            wavfile.write(out / 'audio' / name, RATE, np.int16(np.clip(audio, -1, 1) * 32767))
            # groups are assigned before generation and remain isolated across splits.
            split_bucket = j % 10
            split = 'train' if split_bucket < 7 else ('validation' if split_bucket == 7 else 'test')
            rows.append({'filename': 'audio/' + name, 'label': label, 'split': split,
                         'sample_rate_hz': RATE, 'duration_seconds': duration, 'seed': item_seed,
                         'synthetic': True, 'is_verified_attack': False, **features(audio)})
    # deterministic interleaving, each class retains 70/10/20 split for 200/class
    fieldnames = list(rows[0])
    with (out / 'metadata.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    (out / 'DATASET_CARD.md').write_text('''# NUIT Guard Synthetic Near-Ultrasound Audio Dataset\n\nThis dataset contains **synthetic educational test signals**, not real NUIT attacks or human speech recordings. It contains no voice commands or functional attack payloads.\n\n## Categories\n- `speech_like`: harmonic speech-like signals, not actual voices\n- `background_noise`: filtered random noise\n- `high_frequency`: harmless high-frequency tones\n- `mixed`: low-frequency and high-frequency components combined\n- `nuit_like_simulated`: synthetic signal with intentionally correlated high-frequency and low-frequency components, intended to model a simplified detector signature\n\n## Intended use\nTest signal processing pipelines and establish a *synthetic* benchmark for security-themed audio classification. Results do not establish performance on real NUIT attacks.\n\n## Data generation\nPython, NumPy, SciPy, fixed sample rate 48,000 Hz, 16-bit mono WAV. Reproduce with `generate_dataset.py --count 1000 --seed 2026`. No external recordings.\n\n## Splits and caveats\nThe `split` field gives deterministic 70/10/20 splits for 1,000 records. All examples are algorithmically generated and may share distinctive artifacts across partitions; high scores can reflect generator shortcuts. Evaluate against independent recording conditions and hardware before making security claims.\n\n## License\nGenerated code and data may be released under CC0-1.0 by the creator. Attribute the original NUIT research paper separately.\n''')
    print(f'Generated {len(rows)} WAV files in {out} (labels: {LABELS})')
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='dataset_tools/kaggle_upload')
    parser.add_argument('--count', type=int, default=1000)
    parser.add_argument('--seed', type=int, default=2026)
    parser.add_argument('--duration', type=float, default=1.0)
    args = parser.parse_args()
    generate(args.output, args.count, args.seed, args.duration)

if __name__ == '__main__':
    main()
