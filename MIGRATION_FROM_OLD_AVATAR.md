# Migration & Integration Guide: Member 2 Chacha Chaudhary Avatar

## 1. Overview
This document outlines the integration of the **Member 2 Digital Avatar + Voice System** into the **Ganga AI Mascot** repository, replacing the legacy placeholder avatar runtime with the high-fidelity 3D Chacha Chaudhary character while **strictly preserving 100% of preexisting files and assets**.

---

## 2. Non-Destructive Preservation Policy
- **Zero Deleted Files**: No legacy file was deleted or physically removed (`git diff --name-status` shows 0 deleted files).
- **Preserved Directories**:
  - `avatar/07_Unity/`: Legacy Unity WebGL / assets preserved intact.
  - `avatar/08_Final/`: Previous export attempts preserved intact.
  - `avatar/09_LocalMock/`: Previous local mocks preserved intact.
  - `avatar/05_Voice/`: Previous audio samples preserved intact.
- **Backward Compatibility**:
  - All existing FastAPI endpoints (`/ask`, `/health`, `/api/integration/ask`, `/api/integration/stt`) remain fully functional.
  - Legacy animation alias mappings (`explaining` -> `point`, `namaste` -> `thankful`, `greet` -> `wave`) ensure old clients continue to work without breaking changes.
  - RMS amplitude frames (`rms_lip_sync`) remain available in `AvatarPresentation` alongside phonetic `rhubarb_lipsync`.

---

## 3. Active Runtime Changes

| Component | Legacy Runtime | Member 2 Production Runtime |
| :--- | :--- | :--- |
| **3D Model Format** | FBX loader (`08_Final/final_character.fbx`) | Binary glTF 2.0 (`avatar/Member2_Chacha/Chacha_Master.glb`) |
| **Rig & Skeleton** | Generic / Partial rig | 57-bone standard Mixamo armature (`mixamorig:Hips` -> toes) |
| **Geometry** | Unverified / Partial | 60,000 unique 3D positions (120,000 tris / 119,507 draw vertices) |
| **Facial Controls** | Basic 2-3 morph targets / RMS | 35 Shape Keys (11 modular, 7 emotions, 16 phonetic visemes) |
| **Blinking** | Static or missing | Procedural natural blinking (3–7s interval, 150ms duration) |
| **Animation Clips** | 2-3 basic clips | 9 Mixamo body actions embedded directly in GLB |
| **Speech-to-Text** | Web Speech API or Mock | Offline Vosk Kaldi speech recognition (English + Hindi) |
| **Text-to-Speech** | Browser SpeechSynthesis or pure tone | Neural EdgeTTS (`en-IN-PrabhatNeural`, `hi-IN-MadhurNeural`) + SAPI fallback |
| **Lip-Sync** | Sinusoidal / RMS amplitude gate | Acoustic Rhubarb Lip Sync (phonetic viseme timeline) |

---

## 4. How to Run the Active System

### Prerequisites
- Python 3.11+ (tested on Python 3.13)
- Modern web browser with WebGL support

### Step 1: Start the Integration Server
```bash
# From repository root
python -m integration.server --port 8080
```

### Step 2: Open the Web UI
Navigate to `http://localhost:8080/` in your browser.
- The 3D scene loads `avatar/Member2_Chacha/Chacha_Master.glb`.
- Click the microphone button to record audio in Hindi or English (transcribed via local Vosk STT).
- Type questions in the text input box.
- The avatar responds with neural voice audio, phonetic lip-sync, composite emotion blendshapes, and body gestures.

### Step 3: Run the Automated Verification Suite
```bash
python -m pytest integration/tests
```
All 25 automated tests will execute and verify model integrity, mappers, STT/TTS adapters, and end-to-end conversation flows.
