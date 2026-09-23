# Member 2: Chacha Chaudhary Digital Avatar + Voice System

## 1. Overview
This directory contains the production assets, runtime modules, and configuration for the **Chacha Chaudhary Digital Avatar & Voice System** (Member 2), integrated into the Ganga AI Mascot application.

The avatar serves as the active real-time 3D character delivering conversational responses with full skeletal body animation, facial blendshapes, procedural natural blinking, local offline speech-to-text (STT), high-fidelity neural text-to-speech (TTS), and acoustic phoneme lip-sync.

---

## 2. Master Assets
- **`Chacha_Master.glb`** (101.33 MB):
  - Binary glTF 2.0 WebGL production avatar.
  - **Armature**: Standard 57-bone Mixamo skeletal rig (`mixamorig:Hips` through `mixamorig:RightToe_End`).
  - **Geometry**: 60,000 unique 3D vertex positions (120,000 triangular faces / 119,507 indexed draw corner vertices per glTF specification).
  - **Facial Blendshapes (35 Shape Keys)**: Basis + 34 morph targets.
  - **Body Actions (9 Mixamo Clips)**: Preserved as standard glTF animation clips.
- **`Chacha_Master.blend`** (69.75 MB):
  - Authoritative Blender 3.6 LTS master file.
- **`MEMBER2_GLB_VALIDATION.md`**:
  - Independent verification certification of geometry, bones, shape keys, and action clips.
- **`viseme_mapping.json`**:
  - Acoustic phoneme-to-viseme mapping matrix for Rhubarb Lip Sync in English and Hindi.

---

## 3. Facial Morph Target System (35 Shape Keys)
All morph targets are accessible via Three.js `mesh.morphTargetDictionary` and `mesh.morphTargetInfluences`:

### A. Modular Facial Expressions (11)
- `Blink_L`, `Blink_R`: Independent eyelid blinking. Controlled by procedural blink engine (3–7s interval, 150ms duration).
- `Brow_Raise`, `Brow_Furrow`: Eyebrow modulation.
- `Eyes_Squint`, `Eyes_Wide`: Eye shape variation.
- `Mouth_Smile`, `Mouth_Frown`: Mouth corners.
- `Mouth_Open`, `Mouth_O`, `Jaw_Drop`: Jaw and mouth aperture.

### B. Composite Emotions (7)
- `Emotion_Happy`
- `Emotion_Sad`
- `Emotion_Angry`
- `Emotion_Surprised`
- `Emotion_Confused`
- `Emotion_Thinking`
- `Emotion_Laughing`

### C. Phonetic Speech Visemes (16)
- `Viseme_A`, `Viseme_E`, `Viseme_I`, `Viseme_O`, `Viseme_U`
- `Viseme_MBP` (bilabial closures: M, B, P)
- `Viseme_FV` (labiodental: F, V)
- `Viseme_L` (alveolar lateral: L)
- `Viseme_DTN` (alveolar plosives/nasal: D, T, N)
- `Viseme_KG` (velar: K, G)
- `Viseme_SHCH` (postalveolar: SH, CH, J)
- `Viseme_R` (rhotic: R)
- `Viseme_S` (alveolar fricatives: S, Z)
- `Viseme_NG` (velar nasal: NG)
- `Viseme_Th` (dental fricative: TH)
- `Viseme_Silence` (neutral resting mouth)

---

## 4. Body Actions (9 Mixamo Clips)
All 9 skeletal body animation clips are embedded in `Chacha_Master.glb` and controlled via `Three.AnimationMixer`:
1. `Chacha_Idle`: Neutral conversational breathing and stance.
2. `Chacha_Nod`: Agreement, affirmation, listening confirmation.
3. `Chacha_Point`: Directing attention, explaining concepts, grounded responses.
4. `Chacha_Shrug`: Uncertainty, unknown query, insufficient evidence.
5. `Chacha_Thinking`: Pondering, processing query.
6. `Chacha_Laughing`: Amused, cheerful, storytelling.
7. `Chacha_Waving`: Greeting, welcome, goodbye.
8. `Chacha_Thankful`: Namaste, gratitude, sign-off.
9. `Chacha_ShakingHands`: Polite greeting, partnership.

*Note on Missing Source FBX*: `HeadShake.fbx` and `Talking.fbx` were absent in original Mixamo sources and have intentionally **NOT** been fabricated.

---

## 5. Voice & Speech Architecture
- **Offline STT**: `VoskSTTAdapter` (`LocalSTTProvider`) uses Kaldi acoustic models for English (`vosk-model-small-en-us-0.15`) and Hindi (`vosk-model-small-hi-0.22`) with Unicode NFC preservation.
- **Neural TTS**: `Member2TTSAdapter` (`EdgeTTSProvider`) synthesizes `en-IN-PrabhatNeural` (Indian English Male) and `hi-IN-MadhurNeural` (Hindi Male Chacha).
- **Offline TTS Fallback**: `LocalSapiTTSProvider` uses Windows SAPI SpeechSynthesizer without internet connection.
- **Phonetic Lip Sync**: `RhubarbLipSyncAnalyzer` (`tools/rhubarb/`) extracts frame-accurate mouth cues from 16kHz mono WAV audio into Chacha's 16 visemes.
- **Client Playback**: Real 16kHz audio playback synchronized with sub-frame Three.js morph target animation.
