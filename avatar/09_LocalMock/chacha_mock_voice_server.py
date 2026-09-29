#!/usr/bin/env python3
"""Local smoke-test server for the Chacha Unity avatar.

The server implements the tiny STT, Brain, and TTS HTTP contracts documented in
07_Unity/README.md using only Python's standard library.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import struct
import wave
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from typing import Any


DEFAULT_LANGUAGE = "hi"


class ChachaMockHandler(BaseHTTPRequestHandler):
    server_version = "ChachaMockVoice/1.0"

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send_json({"ok": True, "service": "chacha-local-mock"})
            return
        self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        if self.path == "/stt":
            self._handle_stt()
            return
        if self.path == "/brain":
            self._handle_brain()
            return
        if self.path == "/tts":
            self._handle_tts()
            return
        self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)

    def _handle_stt(self) -> None:
        body = self._read_body()
        language = _extract_multipart_field(body, "language") or DEFAULT_LANGUAGE
        text = "Namaste Chacha, aaj ka demo shuru karo"
        if language.lower().startswith("en"):
            text = "Hello Chacha, start the demo"
        self._send_json({"text": text, "language": language})

    def _handle_brain(self) -> None:
        payload = self._read_json()
        text = str(payload.get("text", "")).strip()
        language = str(payload.get("language", DEFAULT_LANGUAGE)).strip() or DEFAULT_LANGUAGE
        lowered = text.lower()

        emotion = "happy"
        gesture = "wave"
        response_text = "Namaste beta! Main taiyar hoon. Aaj hum kya seekhenge?"

        if language.lower().startswith("en"):
            response_text = "Hello my child! Chacha is here to guide and help you."
            if any(word in lowered for word in ("think", "how", "ponder", "wonder")):
                emotion = "thinking"
                gesture = "thinking"
                response_text = "Let me ponder this for a moment... An interesting thought."
            elif any(word in lowered for word in ("great", "wonderful", "good", "amazing")):
                emotion = "happy"
                gesture = "happy"
                response_text = "Wonderful news! Keep up the brilliant work."
            elif any(word in lowered for word in ("really", "wow", "surprise", "unbelievable")):
                emotion = "surprised"
                gesture = "turn"
                response_text = "Good heavens! That is truly remarkable!"
        else:
            if any(word in lowered for word in ("think", "soch", "kaise", "how", "batao")):
                emotion = "thinking"
                gesture = "thinking"
                response_text = "Hmm, sochne do beta... Achha sawaal hai."
            elif any(word in lowered for word in ("badhiya", "shabash", "achha", "great", "mast")):
                emotion = "happy"
                gesture = "happy"
                response_text = "Wah beta wah! Yeh toh bahut hi badhiya kaam kiya tumne!"
            elif any(word in lowered for word in ("arre", "sach", "kya", "surprise", "really")):
                emotion = "surprised"
                gesture = "turn"
                response_text = "Arre baap re! Sach mein? Yeh toh kamaal ho gaya!"
            elif any(word in lowered for word in ("theek", "samajh", "nod", "yes", "haan")):
                emotion = "neutral"
                gesture = "nod"
                response_text = "Haan beta, bilkul sahi baat hai. Main samajh gaya."

        self._send_json(
            {
                "text": response_text,
                "language": language,
                "emotion": emotion,
                "gesture": gesture,
            }
        )

    def _handle_tts(self) -> None:
        payload = self._read_json()
        text = str(payload.get("text", "Namaste beta! Main taiyar hoon.")).strip()
        wav_bytes = _get_or_synthesize_voice(text)
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "audio/wav")
        self.send_header("Content-Length", str(len(wav_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(wav_bytes)

    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length", "0") or "0")
        return self.rfile.read(length)

    def _read_json(self) -> dict[str, Any]:
        body = self._read_body()
        if not body:
            return {}
        try:
            value = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_json({"error": "Invalid JSON"}, status=HTTPStatus.BAD_REQUEST)
            return {}
        return value if isinstance(value, dict) else {}

    def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        data = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args: Any) -> None:
        print("%s - %s" % (self.address_string(), format % args))


def _extract_multipart_field(body: bytes, field_name: str) -> str:
    if not body:
        return ""
    marker = ('name="%s"' % field_name).encode("utf-8")
    marker_index = body.find(marker)
    if marker_index < 0:
        return ""
    value_start = body.find(b"\r\n\r\n", marker_index)
    if value_start < 0:
        return ""
    value_start += 4
    value_end = body.find(b"\r\n--", value_start)
    raw_value = body[value_start : value_end if value_end >= 0 else len(body)]
    return raw_value.decode("utf-8", errors="ignore").strip()


def _get_or_synthesize_voice(text: str) -> bytes:
    """Checks for matched pre-rendered high-quality audio clips in 05_Voice, or synthesizes dynamic vocal speech."""
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    voice_dir = os.path.join(root_dir, "05_Voice")
    lowered = text.lower()

    # Pre-rendered voice library mapping
    clip_map = [
        (("namaste", "taiyar", "seekhenge"), "chacha_hi_greeting.wav"),
        (("sochne", "soch", "sawaal"), "chacha_hi_thinking.wav"),
        (("wah", "badhiya", "kaam kiya"), "chacha_hi_happy.wav"),
        (("arre", "baap re", "kamaal"), "chacha_hi_surprised.wav"),
        (("haan", "samajh gaya", "sahi baat"), "chacha_hi_nod.wav"),
        (("hello", "child", "guide"), "chacha_en_greeting.wav"),
        (("ponder", "moment", "interesting"), "chacha_en_thinking.wav"),
        (("wonderful", "brilliant"), "chacha_en_happy.wav"),
        (("heavens", "remarkable"), "chacha_en_surprised.wav"),
    ]

    for keywords, filename in clip_map:
        if any(k in lowered for k in keywords):
            clip_path = os.path.join(voice_dir, filename)
            if os.path.exists(clip_path):
                with open(clip_path, "rb") as f:
                    return f.read()

    # Dynamic acoustic formant speech synthesis fallback for arbitrary text
    return _synthesize_dynamic_chacha_voice(text)


def _synthesize_dynamic_chacha_voice(text: str) -> bytes:
    """Acoustic formant synthesizer generating elderly male vocal resonance for dynamic text."""
    sample_rate = 16000
    pitch_base = 112.0  # Warm chest register for elderly uncle persona

    vowel_formants = {
        "a": (730.0, 1150.0, 2450.0),
        "e": (530.0, 1850.0, 2500.0),
        "i": (320.0, 2150.0, 2800.0),
        "o": (500.0, 920.0, 2400.0),
        "u": (360.0, 890.0, 2350.0),
    }

    words = re.findall(r"[A-Za-z]+|[.,!?;]", text) or ["Namaste", "beta"]
    noise_seed = 123456789

    def next_noise():
        nonlocal noise_seed
        noise_seed = (1103515245 * noise_seed + 12345) & 0x7FFFFFFF
        return (noise_seed / 1073741824.0) - 1.0

    samples = []
    # Pre-speech breath
    for _ in range(int(sample_rate * 0.06)):
        samples.append(next_noise() * 0.01)

    word_idx = 0
    total_words = len([w for w in words if re.match(r"[A-Za-z]", w)])

    for word in words:
        if word in [".", ",", "!", "?", ";"]:
            for _ in range(int(sample_rate * 0.18)):
                samples.append(next_noise() * 0.003)
            continue

        w_lower = word.lower()
        word_idx += 1
        syllables = re.findall(r"[bcdfghjklmnpqrstvwxyz]*[aeiou]+[bcdfghjklmnpqrstvwxyz]*", w_lower) or [w_lower]

        for s_idx, syl in enumerate(syllables):
            v_match = re.search(r"[aeiou]+", syl)
            vowel = v_match.group(0)[0] if v_match else "a"
            f1, f2, f3 = vowel_formants.get(vowel, (600.0, 1300.0, 2400.0))

            duration = 0.17 + 0.02 * len(vowel)
            syl_samples = int(sample_rate * duration)
            base_f0 = pitch_base - (word_idx / max(1, total_words)) * 4.0

            r1_r = math.exp(-math.pi * 80.0 / sample_rate)
            r1_a1 = 2.0 * r1_r * math.cos(2.0 * math.pi * f1 / sample_rate)
            r1_a2 = -r1_r * r1_r
            r1_b0 = 1.0 - r1_r

            r2_r = math.exp(-math.pi * 110.0 / sample_rate)
            r2_a1 = 2.0 * r2_r * math.cos(2.0 * math.pi * f2 / sample_rate)
            r2_a2 = -r2_r * r2_r
            r2_b0 = 1.0 - r2_r

            r3_r = math.exp(-math.pi * 140.0 / sample_rate)
            r3_a1 = 2.0 * r3_r * math.cos(2.0 * math.pi * f3 / sample_rate)
            r3_a2 = -r3_r * r3_r
            r3_b0 = 1.0 - r3_r

            r1_y1 = r1_y2 = r2_y1 = r2_y2 = r3_y1 = r3_y2 = 0.0
            phase = 0.0

            for i in range(syl_samples):
                t_syl = i / syl_samples
                t_glob = len(samples) / sample_rate
                f0 = base_f0 + math.sin(2.0 * math.pi * 4.8 * t_glob) * 2.5
                period = sample_rate / f0

                phase += 1.0
                if phase >= period:
                    phase -= period

                p = phase / period
                if p < 0.42:
                    glottal = 0.5 * (1.0 - math.cos(math.pi * p / 0.42))
                elif p < 0.58:
                    glottal = math.cos(math.pi * (p - 0.42) / 0.32)
                else:
                    glottal = 0.0

                source = glottal + next_noise() * 0.08
                env = math.sin(math.pi * math.pow(t_syl, 0.65))

                y1 = r1_b0 * source + r1_a1 * r1_y1 + r1_a2 * r1_y2
                r1_y2 = r1_y1
                r1_y1 = y1

                y2 = r2_b0 * source + r2_a1 * r2_y1 + r2_a2 * r2_y2
                r2_y2 = r2_y1
                r2_y1 = y2

                y3 = r3_b0 * source + r3_a1 * r3_y1 + r3_a2 * r3_y2
                r3_y2 = r3_y1
                r3_y1 = y3

                out = (y1 + y2 * 0.65 + y3 * 0.28) * env * 0.65
                samples.append(out)

    max_amp = max(abs(s) for s in samples) if samples else 1.0
    gain = 0.82 / max(0.01, max_amp)

    buffer = BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        frames = bytearray()
        for s in samples:
            pcm = int(max(-1.0, min(1.0, s * gain)) * 32767.0)
            frames.extend(struct.pack("<h", pcm))
        wav.writeframes(bytes(frames))
    return buffer.getvalue()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Chacha local mock voice server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), ChachaMockHandler)
    print("Chacha local mock server listening on http://%s:%s" % (args.host, args.port))
    print("Endpoints: /health, /stt, /brain, /tts")
    server.serve_forever()


if __name__ == "__main__":
    main()

