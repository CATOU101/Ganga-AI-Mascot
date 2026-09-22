"""RMS/Amplitude-based Lip-Sync analyzer for avatar mouth openness calculation."""

from __future__ import annotations

import math
import logging

logger = logging.getLogger("integration.lipsync")


class LipSyncAnalyzer:
    """Extracts frame-by-frame mouth openness values (0.0 to 1.0) from raw audio PCM samples using RMS analysis."""

    def __init__(self, frame_size: int = 512, silence_threshold: float = 0.02) -> None:
        self.frame_size = frame_size
        self.silence_threshold = silence_threshold

    def compute_rms_frames(self, pcm_samples: list[float]) -> list[float]:
        """Compute normalized RMS mouth aperture for sequential PCM audio samples."""
        if not pcm_samples:
            return []

        rms_values: list[float] = []
        num_samples = len(pcm_samples)

        for i in range(0, num_samples, self.frame_size):
            chunk = pcm_samples[i : i + self.frame_size]
            if not chunk:
                break
            
            # Calculate RMS value
            sum_sq = sum(sample * sample for sample in chunk)
            rms = math.sqrt(sum_sq / len(chunk))

            # Apply noise floor / silence gate
            if rms < self.silence_threshold:
                aperture = 0.0
            else:
                # Scale & clamp RMS between 0.0 (closed) and 1.0 (fully open)
                aperture = min(1.0, max(0.0, (rms - self.silence_threshold) / 0.35))

            rms_values.append(round(aperture, 3))

        return rms_values
