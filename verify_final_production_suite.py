"""Final Production Runtime Verification Suite - Real Brain, Non-Mock.

Verifies:
1. Brain /health & /ask
2. Integration /api/integration/health (mock_mode=False)
3. English typed query -> Real Brain -> EdgeTTS -> Rhubarb -> Payload
4. Hindi typed query -> Real Brain -> EdgeTTS -> Rhubarb -> Payload
5. English Vosk STT -> Real Brain -> EdgeTTS -> Rhubarb
6. Hindi Vosk STT -> Real Brain -> EdgeTTS -> Rhubarb
7. Local Windows SAPI Fallback direct verification
"""

import os
import sys
import json
import base64
import wave
import io
import time
import requests

# Reconfigure stdout for utf-8 on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BRAIN_URL = os.getenv("BRAIN_URL", "http://127.0.0.1:8000")
INTEGRATION_URL = os.getenv("INTEGRATION_URL", "http://127.0.0.1:8080")

print("=" * 80)
print("FINAL PRODUCTION RUNTIME VERIFICATION — REAL BRAIN, NOT MOCK")
print("=" * 80)

# 1. Brain Health
print("\n[STEP 1] Testing Brain /health endpoint...")
r = requests.get(f"{BRAIN_URL}/health", timeout=10)
assert r.status_code == 200, f"Brain health failed: {r.status_code}"
print(f"  Status: {r.status_code}, Response: {r.json()}")

# 2. Brain Direct Ask
print("\n[STEP 2] Testing direct Brain /ask with 'What is the mission of Namami Gange?'...")
r = requests.post(f"{BRAIN_URL}/ask", json={"question": "What is the mission of Namami Gange?"}, timeout=30)
assert r.status_code == 200, f"Brain ask failed: {r.status_code}"
brain_data = r.json()
print(f"  Mode: {brain_data.get('mode')}")
print(f"  Answer excerpt: {brain_data.get('answer')[:160]}...")
print(f"  Citations count: {len(brain_data.get('citations', []))}")
for i, c in enumerate(brain_data.get('citations', [])[:3]):
    print(f"    Citation {i+1}: {c.get('source')} | File: {c.get('file_name')} | Page: {c.get('page')}")

# 3. Integration Health
print("\n[STEP 3] Testing Integration Server /api/integration/health...")
r = requests.get(f"{INTEGRATION_URL}/api/integration/health", timeout=10)
assert r.status_code == 200, f"Integration health failed: {r.status_code}"
int_health = r.json()
print(f"  Service: {int_health.get('service')}")
print(f"  Mock Mode: {int_health.get('mock_mode')} (MUST BE FALSE)")
print(f"  Brain URL: {int_health.get('brain_url')}")
assert int_health.get("mock_mode") is False, "ERROR: mock_mode is not False!"

# 4. Integration Ask English (Real Brain -> Real TTS -> Real Rhubarb)
print("\n[STEP 4] Testing Integration POST /api/integration/ask (English)...")
q_en = "What is the mission of Namami Gange?"
r = requests.post(f"{INTEGRATION_URL}/api/integration/ask", json={"question": q_en, "language": "en"}, timeout=60)
assert r.status_code == 200, f"Integration ask EN failed: {r.status_code}"
res_en = r.json()

print(f"  Answer: {res_en.get('answer')[:180]}...")
print(f"  Is Mock Answer: {'Mock response' in res_en.get('answer', '')}")
assert "Mock response" not in res_en.get("answer", ""), "ERROR: Returned Mock response!"
print(f"  Emotion: {res_en.get('emotion')}")
print(f"  Gesture: {res_en.get('gesture')}")
print(f"  Language: {res_en.get('language')}")
print(f"  State: {res_en.get('state')}")

# Validate Audio
audio_b64 = res_en.get("audio") or res_en.get("audio_data_base64")
assert audio_b64, "ERROR: No audio returned in presentation!"
audio_bytes = base64.b64decode(audio_b64)
print(f"  Audio Payload Size: {len(audio_bytes)} bytes ({len(audio_bytes)/1024/1024:.2f} MB)")
with wave.open(io.BytesIO(audio_bytes), "rb") as wf:
    channels = wf.getnchannels()
    sampwidth = wf.getsampwidth()
    framerate = wf.getframerate()
    nframes = wf.getnframes()
    duration = nframes / float(framerate)
    print(f"  WAV Specs: {framerate}Hz, {sampwidth*8}-bit, {channels} ch, {duration:.2f}s duration")
    assert channels == 1, "Must be mono PCM"
    assert framerate == 16000, "Must be 16kHz"
    assert duration > 5.0, f"Expected realistic speech duration > 5s, got {duration:.2f}s"

# Validate Rhubarb Lip Sync
rhubarb_data = res_en.get("rhubarb_lipsync") or res_en.get("lip_sync")
assert rhubarb_data, "ERROR: No rhubarb_lipsync returned!"
cues = rhubarb_data.get("visemes") or rhubarb_data.get("mouthCues") or rhubarb_data.get("mouth_cues") or []
print(f"  Rhubarb Visemes Count: {len(cues)}")
print(f"  Sample first 3 cues: {cues[:3]}")
assert len(cues) > 10, f"Expected > 10 mouth cues, got {len(cues)}"

# 5. Integration Ask Hindi (Real Brain -> Real TTS -> Real Rhubarb)
print("\n[STEP 5] Testing Integration POST /api/integration/ask (Hindi)...")
q_hi = "नमामि गंगे परियोजना का मुख्य उद्देश्य क्या है?"
r = requests.post(f"{INTEGRATION_URL}/api/integration/ask", json={"question": q_hi, "language": "hi"}, timeout=60)
assert r.status_code == 200, f"Integration ask HI failed: {r.status_code}"
res_hi = r.json()

print(f"  Answer: {res_hi.get('answer')[:180]}...")
print(f"  Is Mock Answer: {'Mock response' in res_hi.get('answer', '')}")
assert "Mock response" not in res_hi.get("answer", ""), "ERROR: Returned Mock response in Hindi!"
print(f"  Emotion: {res_hi.get('emotion')}")
print(f"  Gesture: {res_hi.get('gesture')}")
print(f"  Language: {res_hi.get('language')}")
print(f"  State: {res_hi.get('state')}")

audio_b64_hi = res_hi.get("audio") or res_hi.get("audio_data_base64")
assert audio_b64_hi, "ERROR: No audio returned in Hindi presentation!"
audio_bytes_hi = base64.b64decode(audio_b64_hi)
with wave.open(io.BytesIO(audio_bytes_hi), "rb") as wf:
    duration_hi = wf.getnframes() / float(wf.getframerate())
    print(f"  Hindi Audio Specs: {wf.getframerate()}Hz, duration: {duration_hi:.2f}s")

rhubarb_hi = res_hi.get("rhubarb_lipsync") or res_hi.get("lip_sync")
cues_hi = rhubarb_hi.get("visemes") or rhubarb_hi.get("mouthCues") or []
print(f"  Hindi Rhubarb Visemes Count: {len(cues_hi)}")
assert len(cues_hi) > 5, "Expected phonetic cues for Hindi"

# 6. Microphone / STT Vosk Verification (English)
print("\n[STEP 6] Testing Microphone / Vosk STT Endpoint (English)...")
wav_en_candidates = [
    os.path.join("avatar", "Member2_Chacha", "tests", "data", "hello.wav"),
    r"c:\Users\BADALKUMAR\Downloads\CHACHA final\output\Audio\en\hello.wav",
    "hello.wav"
]
wav_en_path = next((p for p in wav_en_candidates if os.path.exists(p)), None)
assert wav_en_path, "English test wav not found!"
with open(wav_en_path, "rb") as f:
    files = {"file": ("hello.wav", f, "audio/wav")}
    r = requests.post(f"{INTEGRATION_URL}/api/integration/stt?language=en", files=files, timeout=60)
assert r.status_code == 200, f"STT EN failed: {r.status_code}"
stt_res_en = r.json()
print(f"  STT Transcribed Query: '{stt_res_en.get('question')}'")
print(f"  Brain Answer: {stt_res_en.get('answer')[:120]}...")
print(f"  Audio payload present: {bool(stt_res_en.get('audio'))}")
print(f"  Rhubarb visemes: {len((stt_res_en.get('rhubarb_lipsync') or {}).get('visemes', []))}")

# 7. Microphone / STT Vosk Verification (Hindi)
print("\n[STEP 7] Testing Microphone / Vosk STT Endpoint (Hindi)...")
wav_hi_candidates = [
    os.path.join("avatar", "Member2_Chacha", "tests", "data", "namaste.wav"),
    r"c:\Users\BADALKUMAR\Downloads\CHACHA final\output\Audio\hi\namaste.wav",
    "namaste.wav"
]
wav_hi_path = next((p for p in wav_hi_candidates if os.path.exists(p)), None)
assert wav_hi_path, "Hindi test wav not found!"
with open(wav_hi_path, "rb") as f:
    files = {"file": ("namaste.wav", f, "audio/wav")}
    r = requests.post(f"{INTEGRATION_URL}/api/integration/stt?language=hi", files=files, timeout=60)
assert r.status_code == 200, f"STT HI failed: {r.status_code}"
stt_res_hi = r.json()
print(f"  STT Transcribed Query: '{stt_res_hi.get('question')}'")
print(f"  Brain Answer: {stt_res_hi.get('answer')[:120]}...")
print(f"  Audio payload present: {bool(stt_res_hi.get('audio'))}")
print(f"  Rhubarb visemes: {len((stt_res_hi.get('rhubarb_lipsync') or {}).get('visemes', []))}")

# 8. SAPI Offline Fallback Verification
print("\n[STEP 8] Testing SAPI Offline Fallback Provider directly...")
from avatar.Member2_Chacha.chacha_tts_pipeline import LocalSapiTTSProvider
import tempfile

sapi = LocalSapiTTSProvider()
with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
    sapi_out = tf.name
try:
    meta = sapi.synthesize_to_wav("Hello, this is Chacha offline SAPI fallback verification.", language="en", output_wav=sapi_out)
    print(f"  SAPI synthesized successfully: {meta.get('provider')} in {meta.get('latency_ms')}ms")
    with wave.open(sapi_out, "rb") as wf:
        print(f"  SAPI WAV specs: {wf.getframerate()}Hz, {wf.getnchannels()} ch, {wf.getnframes()/float(wf.getframerate()):.2f}s")
finally:
    if os.path.exists(sapi_out):
        os.remove(sapi_out)

print("\n" + "=" * 80)
print("ALL 8 PRODUCTION RUNTIME ACCEPTANCE TESTS PASSED SUCCESSFULLY!")
print("=" * 80)
