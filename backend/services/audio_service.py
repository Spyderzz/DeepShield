"""Phase 17.2 — Audio Deepfake Detection.

Extracts the audio track from a video with ffmpeg, then applies signal-processing
heuristics (silence ratio, spectral centroid variance, RMS consistency) to produce
an audio_authenticity_score (0–100, higher = more natural/authentic).

AI-generated speech typically exhibits:
  - Near-zero silence between words (no natural breath pauses)
  - Very low spectral-centroid variance (monotone formant trajectory)
  - Unnaturally consistent RMS energy across voiced frames
"""
from __future__ import annotations

import os
import subprocess
import tempfile
from dataclasses import dataclass
from typing import Optional

import numpy as np
from loguru import logger


@dataclass
class AudioAnalysis:
    audio_authenticity_score: float  # 0–100
    has_audio: bool
    duration_s: float
    silence_ratio: float             # fraction of 25ms frames below RMS threshold
    spectral_variance: float         # normalised std of spectral centroid
    rms_consistency: float           # 1 – normalised std of voiced-frame RMS
    notes: str = ""


# ---------------------------------------------------------------------------
# ffmpeg extraction
# ---------------------------------------------------------------------------

def _extract_audio_wav(video_path: str, out_path: str) -> bool:
    """Extract mono 16 kHz WAV from *video_path* into *out_path* via ffmpeg."""
    try:
        result = subprocess.run(
            [
                "ffmpeg", "-y", "-i", video_path,
                "-vn", "-acodec", "pcm_s16le",
                "-ar", "16000", "-ac", "1",
                out_path,
            ],
            capture_output=True,
            timeout=60,
        )
        return result.returncode == 0 and os.path.getsize(out_path) > 0
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as exc:
        logger.warning(f"ffmpeg audio extraction failed: {exc}")
        return False


# ---------------------------------------------------------------------------
# Signal-processing analysis
# ---------------------------------------------------------------------------

def _analyse_wav(wav_path: str) -> AudioAnalysis:
    try:
        from scipy.io import wavfile  # scipy already in requirements
        sr, data = wavfile.read(wav_path)
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"WAV read failed: {exc}")
        return AudioAnalysis(
            audio_authenticity_score=50.0, has_audio=True,
            duration_s=0.0, silence_ratio=0.0,
            spectral_variance=0.0, rms_consistency=0.0,
            notes="wav_read_failed",
        )

    # Flatten stereo → mono
    if data.ndim > 1:
        data = data[:, 0]

    data = data.astype(np.float32) / (np.iinfo(np.int16).max + 1)
    duration_s = float(len(data) / sr)

    if duration_s < 0.1:
        return AudioAnalysis(
            audio_authenticity_score=50.0, has_audio=True,
            duration_s=round(duration_s, 3), silence_ratio=1.0,
            spectral_variance=0.0, rms_consistency=0.0,
            notes="too_short",
        )

    # --- 25ms framing ---
    frame_len = max(1, int(sr * 0.025))
    hop_len = max(1, frame_len // 2)
    frames = [
        data[i: i + frame_len]
        for i in range(0, len(data) - frame_len, hop_len)
    ]
    if not frames:
        return AudioAnalysis(
            audio_authenticity_score=50.0, has_audio=True,
            duration_s=round(duration_s, 3), silence_ratio=1.0,
            spectral_variance=0.0, rms_consistency=0.0,
            notes="no_frames",
        )

    rms_vals = np.array([np.sqrt(np.mean(f ** 2)) for f in frames])

    # Silence ratio
    SILENCE_THRESH = 0.01
    silence_ratio = float(np.mean(rms_vals < SILENCE_THRESH))

    # Spectral centroid variance
    freqs = np.fft.rfftfreq(frame_len, d=1.0 / sr)
    centroids: list[float] = []
    for frame in frames:
        spec = np.abs(np.fft.rfft(frame))
        total = float(np.sum(spec))
        if total < 1e-9:
            continue
        centroids.append(float(np.dot(freqs, spec) / total))

    spec_var = (
        float(np.std(centroids) / (np.mean(centroids) + 1e-6))
        if centroids else 0.0
    )

    # RMS consistency on voiced frames
    voiced = rms_vals[rms_vals >= SILENCE_THRESH]
    if len(voiced) > 0:
        rms_consistency = float(
            1.0 - min(1.0, np.std(voiced) / (np.mean(voiced) + 1e-6))
        )
    else:
        rms_consistency = 0.5

    # --- Heuristic scoring ---
    # Silence score: natural speech has moderate pauses (0.1–0.6).
    #   < 0.05 → no pauses (suspicious); > 0.85 → near-silent (unclear).
    if silence_ratio < 0.05:
        silence_score = 55.0
    elif silence_ratio > 0.85:
        silence_score = 50.0
    else:
        silence_score = 100.0

    # Spectral variance score: natural formant motion gives spec_var > 0.25.
    spec_score = min(100.0, spec_var * 250.0)

    # RMS consistency: > 0.92 = unnaturally even (TTS/vocoder artifact).
    rms_score = 55.0 if rms_consistency > 0.92 else 100.0

    audio_score = float(
        0.30 * silence_score + 0.50 * spec_score + 0.20 * rms_score
    )
    audio_score = max(20.0, min(100.0, audio_score))

    logger.info(
        f"Audio: dur={duration_s:.1f}s silence={silence_ratio:.2f} "
        f"spec_var={spec_var:.4f} rms_cons={rms_consistency:.4f} "
        f"→ audio_score={audio_score:.1f}"
    )

    return AudioAnalysis(
        audio_authenticity_score=round(audio_score, 2),
        has_audio=True,
        duration_s=round(duration_s, 2),
        silence_ratio=round(silence_ratio, 4),
        spectral_variance=round(spec_var, 4),
        rms_consistency=round(rms_consistency, 4),
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_audio(video_path: str) -> Optional[AudioAnalysis]:
    """Extract and analyse the audio track from *video_path*.

    Returns an AudioAnalysis dataclass, or None if no audio track is present
    or if ffmpeg is unavailable.
    """
    tmp_wav: Optional[str] = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as fh:
            tmp_wav = fh.name

        if not _extract_audio_wav(video_path, tmp_wav):
            logger.info("No audio track found or ffmpeg unavailable — skipping audio analysis")
            return None

        return _analyse_wav(tmp_wav)

    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Audio analysis error: {exc}")
        return None

    finally:
        if tmp_wav and os.path.exists(tmp_wav):
            try:
                os.unlink(tmp_wav)
            except OSError:
                pass
