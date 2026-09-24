"""
Chacha Chaudhary - Digital Avatar Voice & Audio Pipeline
Stage 10A: TTS Architecture & WAV Audio Generation

Supports:
- English ("en") and Hindi ("hi")
- Multi-provider abstraction:
  - EdgeTTSProvider (High-quality neural speech, Indian English & Hindi)
  - LocalSapiTTSProvider (100% offline local Windows SAPI fallback)
  - CloudTTSProvider (Extensible interface for ElevenLabs / Azure / GCP)
- Uncompressed 16-bit mono 16kHz PCM WAV output optimized for Rhubarb Lip Sync
- Metadata recording (JSON)
"""

import os
import sys
import json
import wave
import subprocess
from abc import ABC, abstractmethod

class BaseTTSProvider(ABC):
    """Abstract Base Class for TTS Providers."""
    
    @abstractmethod
    def synthesize_to_wav(self, text: str, language: str, voice: str, output_wav: str) -> dict:
        """
        Synthesizes text to an uncompressed 16-bit mono PCM WAV file.
        Returns metadata dict with duration, sample_rate, channels, etc.
        """
        pass

class EdgeTTSProvider(BaseTTSProvider):
    """
    Free neural TTS provider using edge-tts.
    Provides natural human-sounding speech in English and Hindi.
    """
    DEFAULT_VOICES = {
        "en": "en-IN-PrabhatNeural",  # Indian English Male
        "hi": "hi-IN-MadhurNeural"    # Hindi Male (Chacha)
    }

    def __init__(self, python_exe=None, blender_exe=None):
        # Locate python with edge_tts installed
        self.python_exe = python_exe or r"C:\Python313\python.exe"
        if not os.path.exists(self.python_exe):
            self.python_exe = sys.executable

        self.blender_exe = blender_exe or r"C:\Program Files\Blender Foundation\Blender 3.6\blender.exe"

    def synthesize_to_wav(self, text: str, language: str, voice: str = None, output_wav: str = "") -> dict:
        lang = language.lower().strip()
        voice_name = voice or self.DEFAULT_VOICES.get(lang, "en-IN-PrabhatNeural")

        temp_mp3 = output_wav.replace(".wav", "_temp.mp3")
        os.makedirs(os.path.dirname(output_wav), exist_ok=True)

        # 1. Generate MP3 via edge-tts
        gen_script = f"""
import asyncio, edge_tts
async def run():
    comm = edge_tts.Communicate({repr(text)}, {repr(voice_name)})
    await comm.save({repr(temp_mp3)})
asyncio.run(run())
"""
        res = subprocess.run([self.python_exe, "-c", gen_script], capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"EdgeTTS generation failed: {res.stderr}")

        # 2. Convert MP3 to 16-bit 16kHz Mono PCM WAV using Blender aud
        conv_script = f"""
import aud
sound = aud.Sound({repr(temp_mp3)})
sound.write({repr(output_wav)}, 16000, 1, aud.FORMAT_S16, aud.CONTAINER_WAV, 65536)
"""
        conv_res = subprocess.run([self.blender_exe, "--background", "--python-expr", conv_script],
                                  capture_output=True, text=True)
        if conv_res.returncode != 0:
            raise RuntimeError(f"Audio conversion to WAV failed: {conv_res.stderr}")

        # Clean up temporary mp3
        if os.path.exists(temp_mp3):
            try:
                os.remove(temp_mp3)
            except:
                pass

        # 3. Read metadata from generated WAV
        return self._read_wav_info(output_wav, text, lang, voice_name, "EdgeTTS")

    def _read_wav_info(self, wav_path, text, language, voice, provider):
        with wave.open(wav_path, "rb") as w:
            channels = w.getnchannels()
            sample_rate = w.getframerate()
            sample_width = w.getsampwidth()
            n_frames = w.getnframes()
            duration = round(n_frames / float(sample_rate), 4)

        return {
            "file_path": os.path.abspath(wav_path),
            "file_name": os.path.basename(wav_path),
            "file_size_bytes": os.path.getsize(wav_path),
            "text": text,
            "language": language,
            "voice": voice,
            "provider": provider,
            "sample_rate": sample_rate,
            "channel_count": channels,
            "sample_width_bytes": sample_width,
            "duration_seconds": duration,
            "total_frames": n_frames
        }

class LocalSapiTTSProvider(BaseTTSProvider):
    """
    100% offline local TTS provider using Windows SAPI SpeechSynthesizer.
    Produces uncompressed PCM WAV directly without network access.
    """
    DEFAULT_VOICES = {
        "en": "Microsoft David Desktop",
        "hi": "Microsoft David Desktop"  # Fallback if no Hindi SAPI voice installed
    }

    def synthesize_to_wav(self, text: str, language: str, voice: str = None, output_wav: str = "") -> dict:
        lang = language.lower().strip()
        voice_name = voice or self.DEFAULT_VOICES.get(lang, "Microsoft David Desktop")
        os.makedirs(os.path.dirname(output_wav), exist_ok=True)

        ps_script = f"""
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {{
    $synth.SelectVoice('{voice_name}')
}} catch {{}}
$synth.SetOutputToWaveFile('{output_wav}')
$synth.Speak('{text}')
$synth.Dispose()
"""
        res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"Local SAPI TTS failed: {res.stderr}")

        with wave.open(output_wav, "rb") as w:
            channels = w.getnchannels()
            sample_rate = w.getframerate()
            sample_width = w.getsampwidth()
            n_frames = w.getnframes()
            duration = round(n_frames / float(sample_rate), 4)

        return {
            "file_path": os.path.abspath(output_wav),
            "file_name": os.path.basename(output_wav),
            "file_size_bytes": os.path.getsize(output_wav),
            "text": text,
            "language": language,
            "voice": voice_name,
            "provider": "LocalSAPI",
            "sample_rate": sample_rate,
            "channel_count": channels,
            "sample_width_bytes": sample_width,
            "duration_seconds": duration,
            "total_frames": n_frames
        }

class CloudTTSProvider(BaseTTSProvider):
    """
    Extensible interface / stub for future cloud providers (ElevenLabs, Azure, GCP).
    """
    def __init__(self, api_key: str = None, service: str = "ElevenLabs"):
        self.api_key = api_key
        self.service = service

    def synthesize_to_wav(self, text: str, language: str, voice: str = None, output_wav: str = "") -> dict:
        raise NotImplementedError(
            f"CloudTTSProvider ({self.service}) interface is prepared. "
            "Configure cloud API credentials to activate cloud synthesis."
        )

class ChachaTTSPipeline:
    """
    High-level TTS and Audio Pipeline for Chacha Avatar.
    Decoupled from Blender Shape Keys.
    """
    def __init__(self, provider: BaseTTSProvider = None, output_dir: str = None):
        self.output_dir = output_dir or r"c:\Users\BADALKUMAR\Downloads\CHACHA final\Output\Audio"
        self.provider = provider or EdgeTTSProvider()

    def synthesize(self, text: str, language: str = "en", voice: str = None, filename: str = None) -> dict:
        """
        Synthesizes text into a clean WAV audio file and saves matching JSON metadata.
        
        Args:
            text: Speech text (English or Hindi).
            language: "en" or "hi".
            voice: Voice name (optional).
            filename: Target base filename without extension (optional).
            
        Returns:
            dict with audio metadata, audio_path, and metadata_path.
        """
        lang = language.lower().strip()
        lang_dir = os.path.join(self.output_dir, lang)
        os.makedirs(lang_dir, exist_ok=True)

        if not filename:
            # Generate clean filename from text or hash
            safe_text = "".join(c for c in text[:20] if c.isalnum() or c in (' ', '_', '-')).strip()
            safe_text = safe_text.replace(' ', '_') or "speech"
            filename = safe_text

        wav_path = os.path.join(lang_dir, f"{filename}.wav")
        json_path = os.path.join(lang_dir, f"{filename}.json")

        # Synthesize audio to WAV
        meta = self.provider.synthesize_to_wav(text=text, language=lang, voice=voice, output_wav=wav_path)
        meta["metadata_path"] = os.path.abspath(json_path)

        # Save metadata JSON
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)

        return meta
