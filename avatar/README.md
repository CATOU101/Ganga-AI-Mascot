# Chacha AI Digital Avatar & Voice System

> **Student Project — Member 2: Digital Avatar + Voice System**  
> An interactive, dependency-free 3D digital avatar of **Chacha** built for Unity 2021.3+, featuring authentic elderly uncle vocal synthesis (Hindi & English), amplitude-based lip sync, and complete local mock Brain/STT/TTS backend integration.

---

## ⚡ Quick Start in 30 Seconds

### 1. Run the 1-Click Automated Verification Suite
Verify all 3D assets, 18 voice clips, 9 C# scripts, Unity materials/scenes, and live mock server API endpoints with one command:
```powershell
python tools\run_all_tests.py
```
*(All 57/57 tests passing 100.0%)*

### 2. Start the Local Mock Voice Server
```powershell
python 09_LocalMock\chacha_mock_voice_server.py --host 127.0.0.1 --port 8765
```
Endpoints active: `GET /health`, `POST /stt`, `POST /brain`, `POST /tts`

### 3. Open and Play in Unity
1. Open **Unity Hub** -> Click **Open** -> select the `07_Unity` folder in this repository.
2. Open `Assets/ChachaAvatar/Scenes/ChachaDemo.unity`.
3. Press **Play** (▶) to interact with Chacha using the on-screen controller panel, keyboard shortcuts (`1-5`, `N`, `W`, `T`, `Space`), or push-to-talk microphone.

---

## 📁 Repository Directory Structure

| Folder | Contents | Description |
|---|---|---|
| [`01_Reference/`](01_Reference/) | Source 3D reference mesh & concept art | `Chacha_Mixamo.fbx`, character concept art |
| [`02_Character/`](02_Character/) | Raw 3D character assets | Base Blender character files |
| [`03_Rig/`](03_Rig/) | Armature & Rigging documentation | [`PHASE1_Rigging_Report.md`](03_Rig/PHASE1_Rigging_Report.md) |
| [`04_Animations/`](04_Animations/) | Skeletal animations & blendshapes | [`PHASE2_Animation_Report.md`](04_Animations/PHASE2_Animation_Report.md), [`PHASE3_Facial_Animation_Report.md`](04_Animations/PHASE3_Facial_Animation_Report.md) |
| [`05_Voice/`](05_Voice/) | Elderly uncle voice library (Hindi & English) | 9 16kHz mono WAV clips + [`PHASE4_Voice_System_Report.md`](05_Voice/PHASE4_Voice_System_Report.md) |
| [`06_LipSync/`](06_LipSync/) | Audio-synchronized mouth animation | [`PHASE5_LipSync_Report.md`](06_LipSync/PHASE5_LipSync_Report.md) |
| [`07_Unity/`](07_Unity/) | Complete Unity 2021.3+ Project | Scenes, Materials, Prefabs, Scripts, Editor Wizard, and [`07_Unity/README.md`](07_Unity/README.md) |
| [`08_Final/`](08_Final/) | Production delivery files & verification renders | `Chacha_Rigged.blend`, `Chacha_Rigged.fbx`, [`FINAL_SUBMISSION_REPORT.md`](08_Final/FINAL_SUBMISSION_REPORT.md) |
| [`09_LocalMock/`](09_LocalMock/) | Zero-dependency local mock server | `chacha_mock_voice_server.py` and [`09_LocalMock/README.md`](09_LocalMock/README.md) |
| [`tools/`](tools/) | Python pipeline & automation tools | `rig_chacha_avatar.py`, `generate_chacha_voice_library.py`, `run_all_tests.py` |

---

## 🎭 Character Features & Technical Specifications

### 1. 3D Model & Armature (Blender -> FBX -> Unity)
- **Armature**: `Chacha_Humanoid_Armature` with 23 bones.
- **Posture**: Right hand permanently weighted to polished wooden walking stick; left hand free for fluid conversational gestures.
- **Materials**: 9 authentic Standard Unity materials:
  `Chacha_Skin`, `Chacha_Turban_Red`, `Chacha_Moustache_White`, `Chacha_Shirt_White`, `Chacha_Vest_Dark`, `Chacha_Tie_Red`, `Chacha_Pants_Navy`, `Chacha_Shoes_Black`, `Chacha_Cane_Brown`.

### 2. Facial Blendshapes & Animation Takes
- **6 Facial Shape Keys**: `Basis`, `Face_Happy` (smile), `Face_Thinking` (raised/furrowed brow), `Face_Surprised` (wide eyes), `Face_SadConfused` (empathy), `Mouth_Open` (lip-sync aperture).
- **7 Skeletal Animation Takes**:
  - `Idle_Breathing` (looping idle posture)
  - `Talking_UpperBody` (active conversational upper-body motion)
  - `Head_Nod` (one-shot pitch nod)
  - `Head_Turn` (curious gaze shift)
  - `Simple_Hand_Gesture` (left-hand wave/gesture)
  - `Happy_Reaction` (chest expansion & cheerful greeting)
  - `Thinking_Reaction` (reflective pose)

### 3. Elderly Uncle Voice Synthesis & Library
- Acoustic 3-formant vocal tract resonator with Rosenberg glottal excitation model ($F_0 \approx 110\text{ Hz}$ elderly pitch, natural vibrato, and vocal fry).
- 9 pre-rendered WAV clips (16,000 Hz, 16-bit Mono PCM) in both Hindi and English:
  - **Hindi**: Greeting (*"Namaste beta..."*), Happy (*"Wah beta wah, shabash!"*), Thinking (*"Hmm, sochte hain..."*), Surprised (*"Arre baap re!"*), Nod (*"Haan haan bilkul..."*).
  - **English**: Greeting (*"Hello child, blessings to you."*), Happy (*"Wonderful, I am very pleased!"*), Thinking (*"Hmm, let me ponder this wisdom..."*), Surprised (*"Goodness gracious, what a revelation!"*).
- Offline fallback: Unity plays authentic voice lines immediately even if the mock server is offline!

### 4. Amplitude Lip-Sync (`AudioMouthLipSync.cs`)
- Samples audio amplitude RMS in real-time from Unity's `AudioSource` to drive `Mouth_Open`.
- Smooth attack/release filter with silence threshold.
- Procedural speech flap fallback oscillates mouth if testing talking state without an audio server.

### 5. Interactive Testing UI (`ChachaTestUI.cs`)
- **State Buttons**: `Idle [1]`, `Talk [2]`, `Happy [3]`, `Thinking [4]`, `Surprised [5]`
- **Gestures**: `Nod [N]`, `Wave [W]`
- **Language Switcher**: Instant toggle between `Hindi (HI)` and `English (EN)`.
- **Conversational Testing**:
  - Custom user text input box with `[Send]`.
  - Push-to-Talk microphone button (`T`).
  - Pipeline test button (`Space`).

---

## 🤝 Team Responsibilities (Member 1 vs. Member 2)

- **Member 2 (Completed)**:
  - 3D character rigging, weighting, materials, blendshapes, and animations.
  - Unity scenes, lighting, camera framing, animator controller, and prefab.
  - Avatar state controller, audio playback, and real-time lip-sync.
  - Elderly voice synthesis model & voice library (Hindi & English).
  - Local mock server (`/health`, `/stt`, `/brain`, `/tts`) for independent testing.
  - Master automated test suite (`run_all_tests.py`).
- **Member 1 (Future / Companion Backend)**:
  - Connects production LLM Brain backend to the `/brain` endpoint contract:
    - Input: `{"text": "user message", "language": "hi"}`
    - Output: `{"text": "response", "language": "hi", "emotion": "happy", "gesture": "wave"}`
  - Connects production STT/TTS services if cloud APIs are desired.

---

## 📊 Verification & Test Status

Run the automated verification suite from the terminal:
```powershell
python tools\run_all_tests.py
```
Full verification matrix:
- **Assets & 3D Model**: 10/10 PASS
- **Voice Library WAVs**: 18/18 PASS
- **C# Script Syntax (Lexical Scanner)**: 9/9 PASS
- **Unity Materials & Scenes**: 13/13 PASS
- **Mock Server API**: 7/7 PASS
- **TOTAL**: **57 / 57 CHECKS PASSED (100.0%)**
- Detailed report: [`08_Final/FINAL_SUBMISSION_REPORT.md`](08_Final/FINAL_SUBMISSION_REPORT.md)
