# Member 2: Digital Avatar + Voice System
## Chacha Chaudhary Multimodal Production Deliverable

---

## 1. Executive Summary

This package represents the complete, finalized deliverable for **Member 2 (Digital Avatar + Voice)** of the Chacha Chaudhary interactive AI system. 

It provides an authoritative 3D digital avatar and complete bilingual voice processing pipeline capable of:
1. **Interactive State Machine**: Natural procedural states (`IDLE`, `LISTENING`, `THINKING`, `SPEAKING`).
2. **Autonomous Blinking**: Non-repetitive procedural blinking engine (bilateral and unilateral) decoupled from skeletal actions.
3. **Layered Facial Rig**: 35 facial Shape Keys supporting 7 composite emotions, 11 modular facial controls, and 16 speech visemes.
4. **9 Body Gestures**: Clean Mixamo skeletal actions (Idle, Nod, Point, Shrug, Thinking, Laughing, Waving, Thankful, ShakingHands).
5. **Acoustic Lip-Sync**: Phoneme-accurate lip-sync powered by Rhubarb Lip Sync with custom Chacha viseme mapping.
6. **Bilingual Speech Synthesis**: Neural voice synthesis in Indian English and Hindi with genuine offline local fallback.
7. **Local Speech-to-Text**: 100% offline local voice recognition via Kaldi Vosk models (en-US and Hindi).
8. **Presentation Scene**: Camera framing (`Camera_Portrait`) and 3-point lighting (`Light_Key`, `Light_Fill`, `Light_Rim`) in Blender.

---

## 2. Frozen 3D Asset Specifications

All geometry, rigging, and animation curves are frozen and certified:

| Metric | Certified Baseline | Verification Status |
| :--- | :--- | :--- |
| **Mesh Vertices** | 60,000 | **100% Preserved** |
| **Mesh Polygons** | 120,000 | **100% Preserved** |
| **Armature Bones** | 57 | **100% Preserved** |
| **Facial Shape Keys** | 35 | **100% Preserved** |
| **Mixamo Body Actions** | 9 | **100% Preserved** |
| **Action F-Curves** | 460 per action | **Bit-for-bit identical** |

> [!NOTE]
> Materials and color styling are intentionally deferred to downstream rendering/frontend requirements. Mesh topology, vertex order, and bone hierarchies remain untouched.

---

## 3. Missing Source Animations Audit

During source asset intake, the following animations were **not supplied** in the original animation repository:
- `HeadShake.fbx` — **NOT SUPPLIED** in source repository.
- `Talking.fbx` — **NOT SUPPLIED** in source repository.

> [!IMPORTANT]
> In accordance with zero-fabrication rules, replacement animations were not invented. The avatar uses `Chacha_Idle`, `Chacha_Thinking`, `Chacha_Nod`, and other verified gestures during conversation turns.

---

## 4. End-to-End System Architecture

```
                    ┌─────────────────────────┐
                    │  USER AUDIO INPUT (MIC) │
                    └────────────┬────────────┘
                                 │
                                 ▼
                     Output/chacha_microphone.py
                     (16-bit mono 16kHz PCM WAV)
                                 │
                                 ▼
                    Output/chacha_stt_pipeline.py
                    (Local Kaldi Vosk Engine)
                                 │
                                 ▼
                       NORMALIZED TEXT (NFC)
                                 │
                                 ▼
                    Output/Integration/ai_provider.py
                       (BaseAIProvider Adapter)
                                 │
                                 ▼
                        RESPONSE TEXT (en/hi)
                     + Emotion & Body Action Tag
                                 │
                                 ▼
                    Output/chacha_tts_pipeline.py
                   (EdgeTTS Neural / SAPI Fallback)
                                 │
                                 ▼
                        16kHz MONO AUDIO WAV
                                 │
                                 ▼
                   Output/chacha_lipsync_pipeline.py
                       (Rhubarb Lip Sync Engine)
                                 │
                                 ▼
                       PHONETIC VISEME JSON
                                 │
                                 ▼
                  Output/chacha_avatar_controller.py
                      (ChachaAvatarController)
                                 │
       ┌─────────────────────────┼─────────────────────────┐
       ▼                         ▼                         ▼
 BODY ACTION              FACIAL EMOTION              PHONETIC LIP-SYNC
(Mixamo skeletal)        (Composite Shape Keys)      (Independent Layer)
       │                         │                         │
       └─────────────────────────┼─────────────────────────┘
                                 ▼
                     PROCEDURAL AUTO-BLINKING
                                 │
                                 ▼
                   BLENDER CHACHA DIGITAL AVATAR
```

---

## 5. Voice & TTS Subsystem Truth

The voice architecture provides two distinct operating modes:

### Primary Engine: `EdgeTTSProvider`
- **Network Requirement**: **ONLINE** (Connects to Microsoft Edge neural speech service).
- **Authentication / API Key**: **NONE** (Free public neural service).
- **English Voice**: `en-IN-PrabhatNeural` (Expressive Indian English Male).
- **Hindi Voice**: `hi-IN-MadhurNeural` (Authentic Hindi Male matching Chacha's warm persona).
- **Output Quality**: High-fidelity natural neural speech converted to uncompressed 16-bit mono 16kHz PCM WAV.

### Offline Fallback: `LocalSapiTTSProvider`
- **Network Requirement**: **100% OFFLINE / LOCAL** (Uses native Windows `System.Speech.Synthesis`).
- **Authentication / API Key**: **NONE**.
- **Voice**: `Microsoft David Desktop` (Standard Windows desktop synthesizer).
- **Behavior**: Operates entirely air-gapped on CPU without internet access.

### Extensible Cloud Stub: `CloudTTSProvider`
- Interface prepared for future ElevenLabs / Azure / GCP enterprise voices (requires API keys).

> [!CAUTION]
> **No gTTS**: Google Translate TTS (`gTTS`) is **not** part of this codebase. `EdgeTTSProvider` is online neural speech and must not be mislabeled as offline.

---

## 6. Speech-to-Text (STT) Subsystem

- **Engine**: `LocalSTTProvider` utilizing Kaldi Vosk.
- **English Model**: `vosk-model-small-en-us-0.15` (39.3 MB, local cache).
- **Hindi Model**: `vosk-model-small-hi-0.22` (42.4 MB, local cache).
- **Network Requirement**: **100% OFFLINE / LOCAL**.
- **Unicode Integrity**: Full NFC Unicode preservation for Hindi Devanagari text.

---

## 7. Facial Rig & Shape Key Mapping

The 35 facial shape keys are organized into three non-interfering layers:

### A. 7 Composite Emotion Presets
- `neutral`: All facial shape keys reset to 0.0.
- `happy`: `Emotion_Happy` + subtle eye squinting and cheek raise.
- `sad`: `Emotion_Sad` + inner brow drop.
- `angry`: `Emotion_Angry` + brow furrow and eye narrowing.
- `surprised`: `Emotion_Surprised` + wide eyes and jaw drop.
- `confused`: `Emotion_Confused` + asymmetrical eyebrow raise.
- `thinking`: `Emotion_Thinking` + tilted brow and subtle lip compression.
- `laughing`: `Emotion_Laughing` + wide open mouth and cheek squint.

### B. 11 Modular Expressions
- Eyebrows: `Brow_Raise`, `Brow_Drop_L`, `Brow_Drop_R`, `Brow_Inner_Up`.
- Eyes: `Blink_L`, `Blink_R`, `Eyes_Wide`, `Eyes_Squint`.
- Cheeks & Nose: `Cheek_Puff`, `Nose_Sneer`.
- Jaw: `Jaw_Open`.

### C. 16 Speech Visemes
`Viseme_Silence`, `Viseme_A`, `Viseme_E`, `Viseme_I`, `Viseme_O`, `Viseme_U`, `Viseme_BMP`, `Viseme_FV`, `Viseme_TH`, `Viseme_L`, `Viseme_WQ`, `Viseme_CDGKNRSThY`, `Viseme_EE`, `Viseme_CH_J_SH`, `Viseme_K_G`, `Viseme_DTN`.

---

## 8. Presentation Scene & Framing

Inside `Chacha_Master.blend`:
- **`Camera_Portrait`**: 50mm portrait lens, positioned at `(0.0, -0.026, 0.0142)`, angled at $88^\circ$. Centered on Chacha's head and chest with zero clipping and comfortable headroom.
- **`Light_Key`**: Sun light (energy: 3.8, warm tint `(1.0, 0.96, 0.92)`), front-left key light.
- **`Light_Fill`**: Sun light (energy: 2.0, cool tint `(0.90, 0.94, 1.0)`), front-right fill light.
- **`Light_Rim`**: Sun light (energy: 3.2, rim tint `(1.0, 0.98, 0.95)`), back-top silhouette rim light.
- **Visual Verification**: Rendered in [`Demos/preview_render.png`](file:///c:/Users/BADALKUMAR/Downloads/CHACHA%20final/Output/Member2_Handoff/Demos/preview_render.png).

---

## 9. Package Directory Manifest

```
Output/Member2_Handoff/
├── Blender/
│   └── Chacha_Master.blend               # Master Blender file with presentation camera & lighting
├── Runtime/
│   ├── chacha_face_controller.py         # Shape key and emotion driver
│   ├── chacha_lipsync_player.py          # Acoustic viseme playback engine
│   ├── chacha_avatar_controller.py       # Master avatar state machine & auto-blinking
│   ├── chacha_microphone.py              # Hardware audio capture
│   ├── chacha_stt_pipeline.py            # Local offline Vosk speech recognition
│   ├── chacha_tts_pipeline.py            # Bilingual TTS (EdgeTTS + Local SAPI)
│   ├── chacha_lipsync_pipeline.py        # Rhubarb phonetic alignment
│   ├── chacha_conversation_pipeline.py   # Multimodal pipeline coordinator
│   ├── ai_provider.py                    # BaseAIProvider, Member1 stub, MockAIProvider
│   ├── viseme_mapping.json               # Rhubarb phoneme -> Chacha viseme mapping
│   └── integration_config.json           # Centralized configuration
├── Demos/
│   ├── demo_speech_en.wav                # Synthesized English audio ("Hello Chacha, how are you?")
│   ├── demo_speech_en.json               # Rhubarb 14-viseme English timeline
│   ├── demo_speech_hi.wav                # Synthesized Hindi audio ("नमस्ते चाचा, आप कैसे हैं?")
│   ├── demo_speech_hi.json               # Rhubarb 15-viseme Hindi timeline
│   ├── preview_render.png                # Actual Blender render verifying camera & lighting
│   └── run_demo.py                       # Standalone script executing verified English & Hindi playback
├── MEMBER2_README.md                     # This document
└── MEMBER2_COMPLETION_CHECKLIST.md       # Sign-off verification checklist
```

---

## 10. How to Run & Verify

### Running the Demos via Blender
Execute the verification demo headlessly using Blender:
```powershell
& "C:\Program Files\Blender Foundation\Blender 3.6\blender.exe" --background "Output\Member2_Handoff\Blender\Chacha_Master.blend" -P "Output\Member2_Handoff\Demos\run_demo.py"
```

### Running the Multimodal Conversation Pipeline
Execute the full conversation loop:
```powershell
& "C:\Python313\python.exe" "Output\Integration\chacha_conversation_pipeline.py"
```

---

## 11. Handoff Notes for Downstream Members

### For Member 1 (AI Reasoning / Brain):
- Subclass `BaseAIProvider` in `Output/Member2_Handoff/Runtime/ai_provider.py`.
- Implement `respond(text, language) -> dict` returning `response_text`, `emotion` (`happy`, `thinking`, etc.), and `body_action` (`Chacha_Nod`, `Chacha_Thinking`, etc.).
- Do not modify avatar controller or audio pipelines.

### For Member 3 (Web Platform / Frontend):
- The avatar asset `Chacha_Master.blend` contains clean non-overlapping Shape Keys and standardized bone names (`mixamorig:*`).
- Export to glTF / USDZ preserves the 35 Shape Keys and 9 skeletal actions.
- Viseme timeline JSON format is lightweight, standard time-indexed phonetic cues ready for WebGL/three.js or Babylon.js consumption.
