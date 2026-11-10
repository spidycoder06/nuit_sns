"""Research-inspired detection of nonlinear ultrasonic speech-like artifacts.

This is a heuristic inspired by Section 8 of Xia et al. (USENIX Security 2023),
NOT an independently validated or production-ready NUIT detector.
"""
from __future__ import annotations

import io
from dataclasses import asdict, dataclass

import numpy as np
import soundfile as sf
from scipy import signal

MAX_SECONDS = 30
MAX_FILE_BYTES = 20 * 1024 * 1024


class AudioValidationError(ValueError):
    pass


def load_audio(data: bytes) -> tuple[np.ndarray, int]:
    if not data or len(data) > MAX_FILE_BYTES:
        raise AudioValidationError("Audio must be nonempty and no larger than 20 MB.")
    try:
        samples, rate = sf.read(io.BytesIO(data), dtype="float64", always_2d=True)
    except Exception as exc:
        raise AudioValidationError("Could not decode audio. Upload a PCM WAV or FLAC file.") from exc
    if rate < 44100:
        raise AudioValidationError("Sample rate must be at least 44,100 Hz to analyze the 16–22 kHz region.")
    if len(samples) / rate > MAX_SECONDS:
        raise AudioValidationError("Audio duration must be 30 seconds or shorter.")
    if len(samples) / rate < 0.15:
        raise AudioValidationError("Audio must be at least 0.15 seconds long.")
    if not np.all(np.isfinite(samples)):
        raise AudioValidationError("Audio contains non-finite samples.")
    if samples.shape[1] > 8:
        raise AudioValidationError("Audio has too many channels.")
    mono = np.mean(samples, axis=1)
    if not np.any(np.abs(mono) > 1e-8):
        raise AudioValidationError("Audio is silent; no signal to analyze.")
    return mono, rate


def bandpass(x: np.ndarray, fs: int, lo: float, hi: float) -> np.ndarray:
    nyq = fs / 2
    high = min(hi, nyq * 0.97)
    if lo >= high:
        return np.zeros_like(x)
    sos = signal.butter(4, [lo, high], btype="bandpass", fs=fs, output="sos")
    return signal.sosfiltfilt(sos, x)


def lowpass(x: np.ndarray, fs: int, cutoff: float) -> np.ndarray:
    sos = signal.butter(4, cutoff, btype="lowpass", fs=fs, output="sos")
    return signal.sosfiltfilt(sos, x)


def rms(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(x * x)))


def series_points(x: np.ndarray, y: np.ndarray, n: int = 450) -> list[dict]:
    if len(x) <= n:
        ind = np.arange(len(x))
    else:
        ind = np.linspace(0, len(x) - 1, n).astype(int)
    return [{"x": round(float(x[i]), 4), "y": round(float(y[i]), 5)} for i in ind]


def analyze(samples: np.ndarray, rate: int, threshold: float = 0.55) -> dict:
    if not 0 < threshold < 1:
        raise AudioValidationError("Threshold must lie strictly between 0 and 1.")
    # Restrict work to modest analysis lengths; 30 s at 48 kHz is supported.
    x = np.asarray(samples, dtype=np.float64)
    high = bandpass(x, rate, 16000, 22000)
    low = bandpass(x, rate, 100, 6000)
    total_energy = float(np.mean(x*x)) + 1e-20
    high_ratio = float(np.mean(high*high) / total_energy)
    # Nonlinear demodulation generates a baseband component related to high-band power.
    # This is only a heuristic comparison: acoustic channels and microphone models vary.
    env = lowpass(high * high, rate, 6000)
    env = bandpass(env, rate, 100, 6000)
    # Downsample for efficient bounded lag correlation while retaining 100..6000 Hz.
    factor = max(1, rate // 16000)
    a = signal.decimate(low, factor, ftype="fir") if factor > 1 else low
    b = signal.decimate(env, factor, ftype="fir") if factor > 1 else env
    reduced_fs = rate / factor
    # Windowed, normalized cross-correlation; tolerate a modest acoustic phase lag.
    window_length = min(len(a), int(reduced_fs * 0.4))
    hop = max(1, window_length // 2)
    max_lag = int(reduced_fs * 0.003)
    coeffs = []
    for start in range(0, len(a) - window_length + 1, hop):
        aa = a[start:start + window_length].copy()
        bb = b[start:start + window_length].copy()
        aa -= aa.mean()
        bb -= bb.mean()
        denom = np.linalg.norm(aa) * np.linalg.norm(bb)
        if denom < 1e-15:
            continue
        # FFT-based correlations rather than repeated O(N^2) operations.
        corr = signal.correlate(aa, bb, mode="full", method="fft") / denom
        mid = len(aa) - 1
        coeffs.append(float(np.max(np.abs(corr[mid-max_lag:mid+max_lag+1]))))
    score = float(np.percentile(coeffs, 75)) if coeffs else 0.0
    detectable_high_band = high_ratio >= 0.005 and rms(high) >= 1e-5
    suspicious = detectable_high_band and score >= threshold
    # Spectrum via Welch to keep memory and CPU bounded.
    freqs, power = signal.welch(x, fs=rate, nperseg=min(8192, len(x)))
    db = 10 * np.log10(power + 1e-14)
    ts = np.arange(len(x)) / rate
    reason = (
        "A measurable near-ultrasound component is correlated with lower-frequency audio, "
        "which is consistent with nonlinear-demodulation artifacts. This is not proof of an attack."
        if suspicious else
        "The tested correlation and high-band energy conditions were not both met. "
        "This does not guarantee that the audio is safe."
    )
    return {
        "verdict": "suspicious" if suspicious else "not_flagged",
        "score": round(score, 4),
        "threshold": threshold,
        "high_band_energy_ratio": round(high_ratio, 6),
        "high_band_rms": round(rms(high), 7),
        "duration_seconds": round(len(x) / rate, 3),
        "sample_rate": int(rate),
        "explanation": reason,
        "method": "High-band power vs. baseband cross-correlation heuristic (research-inspired)",
        "limitations": [
            "Not a validated NUIT exploit detector; a flagged signal can be benign.",
            "Non-flagged audio may still contain threats; sample rate and recording hardware matter.",
            "Browser playback, lossy compression and typical microphone filtering can remove near-ultrasound content.",
            "Correlation thresholds are illustrative, not calibrated for security decisions."
        ],
        "waveform": series_points(ts, x),
        "spectrum": series_points(freqs / 1000.0, db),
        "window_scores": [{"x": round(i * hop/reduced_fs, 3), "y": round(c, 4)} for i,c in enumerate(coeffs)][:120],
    }


def make_demo(kind: str, rate: int = 48000, seconds: float = 2.0) -> bytes:
    """Generate NON-VOICE test signals, not actionable assistant commands."""
    t = np.arange(round(rate * seconds)) / rate
    fade = np.minimum(1, t*20) * np.minimum(1, (seconds-t)*20)
    base = 0.16*np.sin(2*np.pi*430*t) + 0.10*np.sin(2*np.pi*780*t)
    if kind == "normal":
        audio = base * fade
    elif kind == "harmless_high":
        audio = (base + 0.11*np.sin(2*np.pi*18500*t)) * fade
    elif kind == "simulated_nonlinear":
        # Benign tonal modulation; simulated microphone square-law response.
        carrier = (0.19 + 0.08*np.sin(2*np.pi*430*t) + 0.05*np.sin(2*np.pi*780*t)) * np.sin(2*np.pi*18500*t)
        audio = (carrier + 3.5*carrier**2) * fade
        audio -= np.mean(audio)
    else:
        raise AudioValidationError("Unknown demo kind.")
    out = io.BytesIO()
    sf.write(out, np.clip(audio, -0.95, 0.95), rate, format="WAV", subtype="PCM_24")
    return out.getvalue()
