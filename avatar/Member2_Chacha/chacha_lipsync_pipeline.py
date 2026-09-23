"""
Chacha Chaudhary - Digital Avatar Lip-Sync Pipeline
Stage 10B: Audio -> Viseme Timeline & Lip-Sync Analysis

Uses Rhubarb Lip Sync 1.14.0 acoustic analysis engine to extract phonetic
mouth cues from 16-bit mono PCM WAV audio and maps them into Chacha's
16-viseme target system.
"""

import os
import sys
import json
import wave
import subprocess

class ChachaLipSyncPipeline:
    def __init__(self, rhubarb_bin=None, mapping_config_path=None):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        project_dir = os.path.dirname(base_dir)

        # 1. Locate Rhubarb Lip Sync binary
        self.rhubarb_bin = rhubarb_bin or os.path.join(
            project_dir, "tools", "rhubarb", "Rhubarb-Lip-Sync-1.14.0-Windows", "rhubarb.exe"
        )
        if not os.path.exists(self.rhubarb_bin):
            raise FileNotFoundError(f"Rhubarb executable not found at: {self.rhubarb_bin}")

        # 2. Load Mapping Configuration
        config_path = mapping_config_path or os.path.join(base_dir, "viseme_mapping.json")
        with open(config_path, "r", encoding="utf-8") as f:
            self.mapping_config = json.load(f)

        self.allowed_visemes = set(self.mapping_config.get("chacha_allowed_visemes", []))

    def analyze_audio(self, audio_path: str, language: str = "en", transition_ms: float = 50.0) -> dict:
        """
        Analyzes a WAV audio file and produces a Chacha viseme timeline.
        
        Args:
            audio_path: Path to the 16-bit mono PCM WAV file.
            language: "en" or "hi".
            transition_ms: Configurable smoothing/crossfade duration in ms (default: 50.0).
            
        Returns:
            dict with audio_file, language, duration_seconds, transition_ms, and visemes list.
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        lang = language.lower().strip()

        # 1. Measure exact audio duration from WAV header
        with wave.open(audio_path, "rb") as w:
            sample_rate = w.getframerate()
            n_frames = w.getnframes()
            exact_duration = round(n_frames / float(sample_rate), 4)

        # 2. Run Rhubarb Lip Sync in JSON format
        cmd = [self.rhubarb_bin, "-f", "json", audio_path]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"Rhubarb execution failed: {proc.stderr}")

        # Parse JSON output from Rhubarb (starts after any header lines)
        stdout_text = proc.stdout
        json_start_idx = stdout_text.find("{")
        if json_start_idx == -1:
            raise ValueError(f"No JSON found in Rhubarb output: {stdout_text}")

        rhubarb_data = json.loads(stdout_text[json_start_idx:])
        raw_cues = rhubarb_data.get("mouthCues", [])

        # 3. Select mapping dictionary
        mapping_key = f"rhubarb_to_chacha_{lang}"
        mapping = self.mapping_config.get(mapping_key, self.mapping_config["rhubarb_to_chacha_en"])

        # 4. Map cues to Chacha visemes & merge consecutive identical segments
        processed_visemes = []
        for cue in raw_cues:
            start_t = round(float(cue["start"]), 3)
            end_t = round(float(cue["end"]), 3)
            raw_val = cue["value"]

            # Clamp boundaries
            start_t = max(0.0, start_t)
            end_t = min(exact_duration, max(start_t + 0.001, end_t))

            # Map to target viseme
            target_viseme = mapping.get(raw_val, "Silence")
            if target_viseme not in self.allowed_visemes:
                target_viseme = "Silence"

            # Merge with previous if identical
            if processed_visemes and processed_visemes[-1]["viseme"] == target_viseme:
                processed_visemes[-1]["end"] = end_t
            else:
                processed_visemes.append({
                    "start": start_t,
                    "end": end_t,
                    "viseme": target_viseme,
                    "intensity": 1.0
                })

        # Ensure timeline extends to full audio duration
        if processed_visemes:
            if processed_visemes[-1]["end"] < exact_duration:
                # Add trailing silence if needed
                if processed_visemes[-1]["viseme"] == "Silence":
                    processed_visemes[-1]["end"] = exact_duration
                else:
                    processed_visemes.append({
                        "start": processed_visemes[-1]["end"],
                        "end": exact_duration,
                        "viseme": "Silence",
                        "intensity": 1.0
                    })
        else:
            processed_visemes.append({
                "start": 0.0,
                "end": exact_duration,
                "viseme": "Silence",
                "intensity": 1.0
            })

        return {
            "audio_file": os.path.abspath(audio_path),
            "language": lang,
            "duration_seconds": exact_duration,
            "transition_ms": transition_ms,
            "visemes": processed_visemes
        }

    def save_lipsync_json(self, result_dict: dict, output_path: str):
        """Saves the viseme timeline dictionary to a formatted JSON file."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result_dict, f, indent=2, ensure_ascii=False)
        return os.path.abspath(output_path)

# Standalone helper functions
def analyze_audio(audio_path: str, language: str = "en", transition_ms: float = 50.0) -> dict:
    pipeline = ChachaLipSyncPipeline()
    return pipeline.analyze_audio(audio_path=audio_path, language=language, transition_ms=transition_ms)

def save_lipsync_json(result_dict: dict, output_path: str):
    pipeline = ChachaLipSyncPipeline()
    return pipeline.save_lipsync_json(result_dict=result_dict, output_path=output_path)
