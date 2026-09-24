"""Acoustic Rhubarb Lip-Sync & RMS Amplitude analyzers for avatar mouth visemes and aperture."""

from __future__ import annotations

import json
import logging
import math
import os
import subprocess
import tempfile
import wave
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("integration.lipsync")


class RhubarbLipSyncAnalyzer:
    """
    Phonetic acoustic lip-sync analyzer wrapping Rhubarb Lip Sync 1.14.0.
    Maps acoustic phonemes to Chacha Chaudhary's 16-viseme blendshape system.
    """

    def __init__(self, rhubarb_bin: Optional[str] = None, mapping_config_path: Optional[str] = None):
        root_dir = Path(__file__).resolve().parents[2]
        member2_dir = root_dir / "avatar" / "Member2_Chacha"

        # Search possible Rhubarb binary locations
        candidates = [
            rhubarb_bin,
            root_dir / "tools" / "rhubarb" / "Rhubarb-Lip-Sync-1.14.0-Windows" / "rhubarb.exe",
            Path(r"c:\Users\BADALKUMAR\Downloads\CHACHA final\tools\rhubarb\Rhubarb-Lip-Sync-1.14.0-Windows\rhubarb.exe"),
        ]
        self.rhubarb_bin = None
        for cand in candidates:
            if cand and Path(cand).exists():
                self.rhubarb_bin = str(cand)
                break

        # Load mapping config
        conf_candidates = [
            mapping_config_path,
            member2_dir / "viseme_mapping.json",
            Path(r"c:\Users\BADALKUMAR\Downloads\CHACHA final\Output\viseme_mapping.json"),
        ]
        self.mapping_config = {}
        for c_conf in conf_candidates:
            if c_conf and Path(c_conf).exists():
                try:
                    with open(c_conf, "r", encoding="utf-8") as f:
                        self.mapping_config = json.load(f)
                    break
                except Exception as err:
                    logger.warning(f"Failed to read mapping config {c_conf}: {err}")

        raw_allowed = self.mapping_config.get("chacha_allowed_visemes", [
            "Silence", "A", "E", "I", "O", "U", "MBP", "FV", "L", "DTN", "KG",
            "SHCH", "R", "S", "NG", "Th"
        ])
        self.allowed_visemes = set()
        for v in raw_allowed:
            self.allowed_visemes.add(v)
            if not v.startswith("Viseme_"):
                self.allowed_visemes.add(f"Viseme_{v}")

    def analyze_audio_file(self, audio_path: str, language: str = "hi", transition_ms: float = 50.0) -> dict[str, Any]:
        """Runs Rhubarb lip sync on a 16kHz WAV file and returns Chacha viseme timeline."""
        if not audio_path or not os.path.exists(audio_path):
            logger.warning(f"[LipSync] Audio file does not exist: {audio_path}")
            return self._build_fallback_timeline(1.5)

        if not self.rhubarb_bin or not os.path.exists(self.rhubarb_bin):
            logger.warning(f"[LipSync] Rhubarb binary not found at {self.rhubarb_bin}. Falling back.")
            return self._build_fallback_timeline(1.5)

        lang = (language or "hi").lower().strip()
        try:
            with wave.open(audio_path, "rb") as w:
                sample_rate = w.getframerate()
                n_frames = w.getnframes()
                exact_duration = round(n_frames / float(sample_rate), 4)

            cmd = [self.rhubarb_bin, "-f", "json", audio_path]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode != 0:
                logger.error(f"[LipSync] Rhubarb process failed: {proc.stderr}")
                return self._build_fallback_timeline(exact_duration)

            stdout_text = proc.stdout
            json_start_idx = stdout_text.find("{")
            if json_start_idx == -1:
                return self._build_fallback_timeline(exact_duration)

            rhubarb_data = json.loads(stdout_text[json_start_idx:])
            raw_cues = rhubarb_data.get("mouthCues", [])

            mapping_key = f"rhubarb_to_chacha_{lang}"
            mapping = self.mapping_config.get(mapping_key, self.mapping_config.get("rhubarb_to_chacha_en", {}))

            processed_visemes = []
            for cue in raw_cues:
                start_t = round(float(cue["start"]), 3)
                end_t = round(float(cue["end"]), 3)
                raw_val = cue["value"]

                start_t = max(0.0, start_t)
                end_t = min(exact_duration, max(start_t + 0.001, end_t))

                target_viseme = mapping.get(raw_val, "Viseme_Silence")
                if not target_viseme.startswith("Viseme_"):
                    target_viseme = f"Viseme_{target_viseme}"
                if target_viseme not in self.allowed_visemes:
                    target_viseme = "Viseme_Silence"

                if processed_visemes and processed_visemes[-1]["viseme"] == target_viseme:
                    processed_visemes[-1]["end"] = end_t
                else:
                    processed_visemes.append({
                        "start": start_t,
                        "end": end_t,
                        "viseme": target_viseme,
                        "intensity": 1.0,
                    })

            if processed_visemes:
                if processed_visemes[-1]["end"] < exact_duration:
                    if processed_visemes[-1]["viseme"] == "Viseme_Silence":
                        processed_visemes[-1]["end"] = exact_duration
                    else:
                        processed_visemes.append({
                            "start": processed_visemes[-1]["end"],
                            "end": exact_duration,
                            "viseme": "Viseme_Silence",
                            "intensity": 1.0,
                        })
            else:
                processed_visemes.append({
                    "start": 0.0,
                    "end": exact_duration,
                    "viseme": "Viseme_Silence",
                    "intensity": 1.0,
                })

            return {
                "audio_file": os.path.abspath(audio_path),
                "language": lang,
                "duration_seconds": exact_duration,
                "transition_ms": transition_ms,
                "visemes": processed_visemes,
                "mouth_cues": processed_visemes,
                "mouthCues": raw_cues,
            }

        except Exception as err:
            logger.error(f"[LipSync] Error during Rhubarb analysis: {err}")
            return self._build_fallback_timeline(2.0)

    def _build_fallback_timeline(self, duration: float) -> dict[str, Any]:
        """Provides natural cadence fallback visemes when audio analysis is bypassed."""
        step = 0.2
        curr = 0.0
        cues = ["Viseme_Silence", "Viseme_A", "Viseme_O", "Viseme_E", "Viseme_MBP", "Viseme_Silence"]
        visemes = []
        idx = 0
        while curr < duration:
            end_t = min(duration, round(curr + step, 3))
            v_name = cues[idx % len(cues)]
            visemes.append({"start": curr, "end": end_t, "viseme": v_name, "intensity": 0.8})
            curr = end_t
            idx += 1

        return {
            "language": "hi",
            "duration_seconds": round(duration, 3),
            "transition_ms": 50.0,
            "visemes": visemes,
            "mouth_cues": visemes,
            "mouthCues": [{"start": v["start"], "end": v["end"], "value": v["viseme"].replace("Viseme_", "")} for v in visemes],
        }


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
            
            sum_sq = sum(sample * sample for sample in chunk)
            rms = math.sqrt(sum_sq / len(chunk))

            if rms < self.silence_threshold:
                aperture = 0.0
            else:
                aperture = min(1.0, max(0.0, (rms - self.silence_threshold) / 0.35))

            rms_values.append(round(aperture, 3))

        return rms_values
