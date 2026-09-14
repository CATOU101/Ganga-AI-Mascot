#!/usr/bin/env python3
"""Chacha AI Avatar - Formant Vocal Tract Synthesizer & Voice Library Generator.

Generates authentic, elderly Indian uncle ("Chacha") speech audio in 16-bit 16kHz WAV format
using acoustic formant synthesis (Rosenberg glottal excitation, vocal tract resonance filters,
and consonant noise modeling).
"""

import math
import os
import re
import struct
import wave

SAMPLE_RATE = 16000

# Vowel Formant Profiles (F1, F2, F3 in Hz) for an elderly adult male vocal tract
VOWEL_FORMANTS = {
    "a": (730.0, 1150.0, 2450.0),
    "aa": (760.0, 1200.0, 2500.0),
    "e": (530.0, 1850.0, 2500.0),
    "ee": (290.0, 2250.0, 2900.0),
    "i": (320.0, 2150.0, 2800.0),
    "o": (500.0, 920.0, 2400.0),
    "oo": (340.0, 850.0, 2300.0),
    "u": (360.0, 890.0, 2350.0),
    "neutral": (500.0, 1500.0, 2500.0),
}

# Formant Bandwidths (Q factors)
BANDWIDTHS = (80.0, 110.0, 140.0)


class SecondOrderResonator:
    """Digital 2nd-order IIR bandpass resonator filter."""

    def __init__(self, frequency: float, bandwidth: float, sample_rate: int = SAMPLE_RATE):
        self.sample_rate = sample_rate
        self.y1 = 0.0
        self.y2 = 0.0
        self.update(frequency, bandwidth)

    def update(self, frequency: float, bandwidth: float):
        r = math.exp(-math.pi * bandwidth / self.sample_rate)
        theta = 2.0 * math.pi * frequency / self.sample_rate
        self.a1 = 2.0 * r * math.cos(theta)
        self.a2 = -r * r
        self.b0 = 1.0 - r

    def process(self, x: float) -> float:
        y0 = self.b0 * x + self.a1 * self.y1 + self.a2 * self.y2
        self.y2 = self.y1
        self.y1 = y0
        return y0


def synthesize_chacha_speech(text: str, pitch_base: float = 112.0) -> bytes:
    """Synthesizes human-like speech for Chacha with elderly pitch, formants, and articulation."""
    words = re.findall(r"[A-Za-z]+|[.,!?;]", text)
    if not words:
        words = ["Namaste"]

    # Simple pseudo-random generator for noise reproducibility without dependencies
    noise_seed = 123456789

    def next_noise():
        nonlocal noise_seed
        noise_seed = (1103515245 * noise_seed + 12345) & 0x7FFFFFFF
        return (noise_seed / 1073741824.0) - 1.0

    samples = []
    r1 = SecondOrderResonator(700.0, 80.0)
    r2 = SecondOrderResonator(1200.0, 110.0)
    r3 = SecondOrderResonator(2500.0, 140.0)

    # Pre-speech breath
    for _ in range(int(SAMPLE_RATE * 0.08)):
        samples.append(next_noise() * 0.012)

    total_words = len([w for w in words if re.match(r"[A-Za-z]", w)])
    word_idx = 0

    for word in words:
        if word in [".", ",", "!", "?", ";"]:
            # Pause on punctuation
            pause_len = int(SAMPLE_RATE * (0.28 if word in [".", "!", "?"] else 0.15))
            for _ in range(pause_len):
                samples.append(next_noise() * 0.003)
            continue

        w_lower = word.lower()
        word_idx += 1

        # Break word into simple vowel/consonant syllables
        syllables = re.findall(r"[bcdfghjklmnpqrstvwxyz]*[aeiou]+[bcdfghjklmnpqrstvwxyz]*", w_lower)
        if not syllables:
            syllables = [w_lower]

        for s_idx, syl in enumerate(syllables):
            # Identify vowel in syllable
            v_match = re.search(r"[aeiou]+", syl)
            vowel = v_match.group(0) if v_match else "a"
            f1, f2, f3 = VOWEL_FORMANTS.get(vowel, VOWEL_FORMANTS.get(vowel[0], VOWEL_FORMANTS["neutral"]))

            # Consonants in syllable
            leading_c = syl[: v_match.start()] if v_match else ""
            trailing_c = syl[v_match.end() :] if v_match else ""

            duration = 0.18 + 0.03 * len(vowel)
            if s_idx == len(syllables) - 1 and word_idx == total_words:
                duration += 0.08  # Sentence-final lengthening

            syl_samples = int(SAMPLE_RATE * duration)

            # Pitch contour: slight downdrift across sentence, gentle vibrato ~4.5Hz
            base_f0 = pitch_base - (word_idx / max(1, total_words)) * 6.0
            if "?" in text and word_idx == total_words:
                base_f0 += 16.0  # Question pitch rise

            phase = 0.0
            for i in range(syl_samples):
                t_syl = i / syl_samples
                t_global = len(samples) / SAMPLE_RATE

                # Chacha vocal vibrato (elderly warm flutter)
                vibrato = math.sin(2.0 * math.pi * 4.8 * t_global) * 2.8
                current_f0 = base_f0 + vibrato

                # Consonant articulation
                is_leading_consonant = i < int(SAMPLE_RATE * 0.035) and len(leading_c) > 0
                is_sibilant = any(c in leading_c or c in trailing_c for c in ["s", "sh", "z", "ch"])
                is_nasal = any(c in leading_c or c in trailing_c for c in ["m", "n"])

                # Rosenberg glottal excitation pulse
                period = SAMPLE_RATE / current_f0
                phase += 1.0
                if phase >= period:
                    phase -= period

                pos_in_period = phase / period
                if pos_in_period < 0.40:
                    # Glottal opening
                    glottal = 0.5 * (1.0 - math.cos(math.pi * pos_in_period / 0.40))
                elif pos_in_period < 0.56:
                    # Glottal closing
                    glottal = math.cos(math.pi * (pos_in_period - 0.40) / 0.32)
                else:
                    glottal = 0.0

                # Add vocal fry and breathiness
                aspiration = next_noise() * (0.09 if not is_sibilant else 0.45)
                source_signal = glottal + aspiration

                # Envelope for syllable
                env = math.sin(math.pi * math.pow(t_syl, 0.65))

                if is_leading_consonant:
                    if is_sibilant:
                        source_signal = next_noise() * 0.5
                    elif is_nasal:
                        f1, f2, f3 = 260.0, 950.0, 2200.0
                    else:
                        # Plosive closure
                        env *= 0.25

                # Process formants
                r1.update(f1, BANDWIDTHS[0])
                r2.update(f2, BANDWIDTHS[1])
                r3.update(f3, BANDWIDTHS[2])

                out1 = r1.process(source_signal)
                out2 = r2.process(source_signal) * 0.65
                out3 = r3.process(source_signal) * 0.28

                vocal_out = (out1 + out2 + out3) * env * 0.60
                samples.append(vocal_out)

        # Inter-word small pause
        for _ in range(int(SAMPLE_RATE * 0.04)):
            samples.append(next_noise() * 0.002)

    # Post-speech trail
    for _ in range(int(SAMPLE_RATE * 0.10)):
        samples.append(next_noise() * 0.003)

    # Normalize and write to WAV bytes
    max_amp = max(abs(s) for s in samples) if samples else 1.0
    gain = 0.85 / max(0.01, max_amp)

    out_frames = bytearray()
    for s in samples:
        val = int(max(-1.0, min(1.0, s * gain)) * 32767.0)
        out_frames.extend(struct.pack("<h", val))

    wav_buffer = bytearray()
    # RIFF header
    data_size = len(out_frames)
    wav_buffer.extend(b"RIFF")
    wav_buffer.extend(struct.pack("<I", 36 + data_size))
    wav_buffer.extend(b"WAVEfmt ")
    wav_buffer.extend(struct.pack("<I", 16))
    wav_buffer.extend(struct.pack("<H", 1))  # PCM
    wav_buffer.extend(struct.pack("<H", 1))  # Mono
    wav_buffer.extend(struct.pack("<I", SAMPLE_RATE))
    wav_buffer.extend(struct.pack("<I", SAMPLE_RATE * 2))  # Byte rate
    wav_buffer.extend(struct.pack("<H", 2))  # Block align
    wav_buffer.extend(struct.pack("<H", 16))  # Bits per sample
    wav_buffer.extend(b"data")
    wav_buffer.extend(struct.pack("<I", data_size))
    wav_buffer.extend(out_frames)

    return bytes(wav_buffer)


def build_voice_library():
    """Builds a curated library of high-fidelity Hindi and English speech clips for Chacha."""
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    voice_dir = os.path.join(root_dir, "05_Voice")
    unity_audio_dir = os.path.join(root_dir, "07_Unity", "Assets", "ChachaAvatar", "Audio")
    os.makedirs(voice_dir, exist_ok=True)
    os.makedirs(unity_audio_dir, exist_ok=True)

    library = [
        # Hindi Voice Clips
        ("chacha_hi_greeting.wav", "Namaste beta! Main taiyar hoon. Aaj hum kya seekhenge?", 110.0),
        ("chacha_hi_thinking.wav", "Hmm, sochne do beta... Achha sawaal hai.", 108.0),
        ("chacha_hi_happy.wav", "Wah beta wah! Yeh toh bahut hi badhiya kaam kiya tumne!", 116.0),
        ("chacha_hi_surprised.wav", "Arre baap re! Sach mein? Yeh toh kamaal ho gaya!", 120.0),
        ("chacha_hi_nod.wav", "Haan beta, bilkul sahi baat hai. Main samajh gaya.", 108.0),
        # English Voice Clips
        ("chacha_en_greeting.wav", "Hello my child! Chacha is here to guide and help you.", 112.0),
        ("chacha_en_thinking.wav", "Let me ponder this for a moment... An interesting thought.", 110.0),
        ("chacha_en_happy.wav", "Wonderful news! Keep up the brilliant work.", 118.0),
        ("chacha_en_surprised.wav", "Good heavens! That is truly remarkable!", 122.0),
    ]

    manifest = {}

    for filename, phrase, pitch in library:
        wav_bytes = synthesize_chacha_speech(phrase, pitch_base=pitch)

        # Write to 05_Voice/
        p_voice = os.path.join(voice_dir, filename)
        with open(p_voice, "wb") as f:
            f.write(wav_bytes)

        # Write to 07_Unity/Assets/ChachaAvatar/Audio/
        p_unity = os.path.join(unity_audio_dir, filename)
        with open(p_unity, "wb") as f:
            f.write(wav_bytes)

        # Write Unity metadata
        import hashlib
        guid = hashlib.md5(("chacha_audio_" + filename).encode()).hexdigest()
        with open(p_unity + ".meta", "w", encoding="utf-8") as f:
            f.write(f"""fileFormatVersion: 2
guid: {guid}
AudioImporter:
  defaultSettings:
    loadType: 0
    sampleRateSetting: 0
    sampleRateOverride: 16000
    compressionFormat: 0
    quality: 1
    conversionMode: 0
  userData: 
  assetBundleName: 
  assetBundleVariant: 
""")

        duration = len(wav_bytes) / (SAMPLE_RATE * 2)
        manifest[filename] = {
            "phrase": phrase,
            "duration_sec": round(duration, 2),
            "size_bytes": len(wav_bytes),
            "pitch_hz": pitch,
        }
        print(f"Synthesized '{filename}': {phrase} ({round(duration, 2)}s)")

    # Also write a manifest report in 05_Voice
    report_path = os.path.join(voice_dir, "PHASE4_Voice_System_Report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Phase 4 - Chacha Digital Voice & TTS Synthesis System\n\n")
        f.write("Date: 2026-09-12\n\n")
        f.write("## Acoustic Character Profile\n\n")
        f.write("- **Persona**: Chacha (warm, respectable, encouraging elderly Indian uncle)\n")
        f.write("- **Fundamental Pitch (F0)**: 105 Hz – 120 Hz (mature male chest register)\n")
        f.write("- **Vocal Tract Resonance**: 3-formant digital resonator modeled after adult male Hindi/English articulation\n")
        f.write("- **Vocal Inflection**: Warm 4.8 Hz flutter vibrato, intonational sentence-final cadence\n")
        f.write("- **Format**: Standard 16 kHz 16-bit Mono PCM WAV (100% offline, zero-paid API dependencies)\n\n")
        f.write("## Voice Library Manifest\n\n")
        f.write("| File | Character Dialogue | Pitch | Duration |\n")
        f.write("|---|---|:---:|:---:|\n")
        for fn, info in manifest.items():
            f.write(f"| `{fn}` | \"{info['phrase']}\" | {info['pitch_hz']} Hz | {info['duration_sec']}s |\n")
        f.write("\n## Integration Architecture\n\n")
        f.write("1. **Mock Voice Server (`09_LocalMock`)**: When requested for speech, the server matches key phrases from this library or dynamically synthesizes vocal formant speech on the fly.\n")
        f.write("2. **Unity Audio (`Assets/ChachaAvatar/Audio/`)**: All clips are imported with AudioImporter settings and mapped into the avatar runtime for instant offline and mock server playback.\n")
        f.write("3. **Lip-Sync (`AudioMouthLipSync`)**: Audio amplitude envelope samples the formant energy peaks to flap `Mouth_Open` synchronously with spoken vowels.\n")

    print(f"\nGenerated {len(library)} voice clips in 05_Voice and Unity Assets/ChachaAvatar/Audio.")
    print(f"Saved Phase 4 report at {report_path}.")


if __name__ == "__main__":
    build_voice_library()
