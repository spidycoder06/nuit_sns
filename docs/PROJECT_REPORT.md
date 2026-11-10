# NUIT Guard — Student Project Report and Viva Notes

## Problem statement
Voice assistants may interpret inaudible, modulated near-ultrasound signals as commands as a result of microphone nonlinearity. Students investigate the frequency-domain signatures associated with an idealized nonlinear audio pathway.

## Objective
Create a full-stack application that analyzes high-resolution audio uploads, computes power-spectral and cross-band statistics, and presents explainable heuristic alerts. Safely explore why naive high-frequency detection yields false positives.

## Reference
Qi Xia, Qian Chen, and Shouhuai Xu, *Near-Ultrasound Inaudible Trojan (NUIT): Exploiting Your Speaker to Attack Your Microphone*, Proceedings of the 32nd USENIX Security Symposium, 2023. Primary ideas: near-ultrasound around 16–22 kHz; microphone nonlinearity; cross-band correlation-based detection in Section 8.

## Architecture
React/Vite UI → HTTP multipart upload → FastAPI → soundfile WAV/FLAC decoder → SciPy filtering, spectral analysis and windowed cross-correlation → JSON output → Recharts visualizations.

## Algorithm
1. Decode PCM WAV/FLAC; enforce limits and sampling bandwidth. Convert to mono.
2. Fourth-order Butterworth band-pass filter 16–22 kHz (truncated below Nyquist) to estimate high-frequency signal `h(t)`.
3. Filter 100–6000 Hz to obtain baseband `b(t)`.
4. Estimate nonlinear output via `h(t)^2`; low-pass then band-pass the squared signal to recover envelope variations.
5. Compute normalized cross-correlation of windowed baseband and envelope, testing ±3 ms lag, using FFT convolution. Extract 75th percentile as an illustrative score.
6. Flag only when high-band energy ratio ≥ 0.005, high-band RMS ≥ 1e-5, and the score exceeds the user-configured threshold (default 0.55).
7. Show waveform and Welch PSD and export a JSON summary.

Note: exact threshold and methodology are student implementation decisions inspired by the paper rather than an assertion of exact replication. A signal can be benign and nonetheless correlate.

## Safe test cases
- Normal benign composite tones.
- Benign composite tones plus an unmodulated high-frequency tone.
- Amplitude-modulated benign high-frequency carrier with simulated quadratic response.
No assistant wake phrase or voice control payload is generated.

## Evaluation plan
Use `pytest -q` to verify endpoints and invalid inputs, then manually check three demo signals in the browser. To assess performance, collect consented and consistently sampled benign and simulated positive signals in separate test groups, report confusion matrix (TP, FP, TN, FN), precision = TP/(TP+FP), recall = TP/(TP+FN), FPR = FP/(FP+TN), and average latency. Do not claim field efficacy from synthetic scores alone.

## Limitations & future enhancements
- No real-time monitoring yet; browser live microphones generally remove high-frequency components.
- Audio uploaded to the API is held in memory but not persisted.
- Heuristic does not recognize command semantics or prove an attack.
- Real NUIT defense would require extensive hardware-specific experimental validation.
- Future research: calibrated thresholds, device profiles, ROC curves, broader recordings, genuine licensed lab datasets, and latency benchmarks.

## Viva Q&A
**What is NUIT?** A near-ultrasound voice-command injection technique using speaker–microphone nonlinear behavior.
**What are NUIT-1 and NUIT-2?** Same-device and cross-device speaker-to-microphone attacks.
**Why require ≥44.1 kHz?** Nyquist limits resolvable frequencies to half the sample rate; low-rate recordings cannot represent near-ultrasound.
**Why square the filtered high-band signal?** Quadratic nonlinearity can generate low-frequency envelope terms from high-frequency energy.
**Why cross-correlation?** It measures similarity of two signals across small time offsets, potentially identifying a shared origin.
**Why doesn't high-band energy imply an attack?** Music, electronic devices, test tones and recording artifacts may contain high frequencies.
**Why can't we guarantee protection?** Algorithm parameters are not calibrated on real attack devices and recording pathways can alter critical frequencies.
