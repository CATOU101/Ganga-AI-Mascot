# Chacha Unity AI Avatar

This project provides an interactive, dependency-free 3D digital avatar of **Chacha** built for Unity 2021.3+, integrated with authentic elderly uncle voice synthesis (Hindi & English) and a local mock Brain/STT/TTS server.

---

## Quick Start (Step-by-Step)

### 1. How to Open the Unity Project
1. Open **Unity Hub**.
2. Click **Open** > **Add project from disk**.
3. Select the `07_Unity` folder inside this repository.
4. Use Unity Editor version **2021.3 LTS** (or later 2021/2022 LTS).

### 2. How to Start the Local Mock Server (Optional for Online Pipeline)
From PowerShell or terminal in the repository root:
```powershell
python 09_LocalMock\chacha_mock_voice_server.py --host 127.0.0.1 --port 8765
```
You should see:
```text
Chacha local mock server listening on http://127.0.0.1:8765
Endpoints: /health, /stt, /brain, /tts
Voice library: 9 pre-rendered clips in 05_Voice/ + acoustic formant synthesizer fallback
```
Confirm health: open `http://127.0.0.1:8765/health` in your browser.

> **Offline Voice Support:** Even if you do **not** run the mock server, Chacha has a built-in pre-rendered local voice library in `Assets/ChachaAvatar/Audio/`. Pressing buttons in Unity will play Chacha's authentic elderly voice lines and lip sync completely offline!

### 3. How to Run the Unity Scene
1. In the Unity Project window, navigate to either:
   - `Assets/ChachaAvatar/Scenes/ChachaDemo.unity` or
   - `Assets/ChachaAvatar/Generated/ChachaDemo.unity`
2. Double-click the scene to open it.
3. Click the **Play** button (▶) at the top of the Unity Editor.
4. The on-screen **Chacha Avatar Controller** test panel appears in the top-left of the Game view.

> **Note:** You can also run `Chacha > 1-Click Complete Setup` from Unity's top menu bar at any time to re-generate or re-link all assets, materials, controllers, voice clips, and scenes automatically.

---

## Testing Avatar States, Gestures & Realistic Voices

When the scene is playing, the on-screen UI provides full interactive control:

### 1. Voice & Language Controls
- **Play Voice Audio with States**: Checkbox toggle (defaults to ON). When active, clicking state buttons automatically triggers Chacha's corresponding voice dialogue with real-time lip-sync!
- **Language Switcher**: Click `Hindi (HI)` or `English (EN)` to switch Chacha's spoken voice and responses.

### 2. Direct State & Gesture Testing
| Button | Key | Spoken Dialogue (HI / EN) | Animation & Facial Blendshape |
|---|:---:|---|---|
| **Idle** | `1` | *(Speech Stops)* | Returns to neutral breathing pose (`Idle_Breathing`), clears expressions. |
| **Talk** | `2` | *(Continuous procedural talk)* | Transitions to talking posture (`Talking_UpperBody`) with natural mouth flap. |
| **Happy** | `3` | *"Wah beta wah, shabash!"* / *"Wonderful, I am very pleased!"* | Activates `Face_Happy` smile blendshape + plays `Happy_Reaction` body gesture. |
| **Thinking** | `4` | *"Hmm, sochte hain..."* / *"Hmm, let me ponder this wisdom..."* | Activates `Face_Thinking` brow blendshape + plays `Thinking_Reaction` gesture. |
| **Surprised** | `5` | *"Arre baap re, yeh kya hua!"* / *"Goodness gracious, what a revelation!"* | Activates `Face_Surprised` blendshape with wide eyes and open brow. |
| **Nod** | `N` | *"Haan haan bilkul, theek hai."* / *"Yes yes, indeed."* | Plays one-shot head nod gesture (`Head_Nod`) acknowledging the user. |
| **Greeting** | `W` | *"Namaste beta, kaise ho?"* / *"Hello child, blessings to you."* | Plays left-hand conversational gesture (`Simple_Hand_Gesture`). |

### 3. End-to-End Pipeline & Conversational Testing
- **Custom User Text Input**: Type any custom phrase or question into the on-screen text box and click `[Send]` to watch Chacha process the request, think, and reply with audio and lip-sync!
- **Microphone Push-to-Talk (`T`)**: Click/hold the `[Hold / Click to Talk (Mic)]` button (or press `T`) to capture live audio from your microphone -> sends to `/stt` -> passes to `/brain` -> streams speech via `/tts`.
- **Direct Pipeline Test (`Space`)**:
  - **If Mock Server is Online**: Sends the message to `/brain` -> receives contextual command & emotion -> requests `/tts` -> plays generated audio -> drives real-time `AudioMouthLipSync` -> smoothly resets to Idle.
  - **If Mock Server is Offline**: Seamlessly falls back to local elderly voice playback and runs the complete lip sync and gesture pipeline, ensuring zero interruptions during testing.

### 4. Master 1-Click Automated Test Suite
To run the automated pre-flight checks across all 3D assets, 18 audio WAV files, 9 C# scripts, Unity materials/scenes, and live mock server API endpoints:
```powershell
python tools\run_all_tests.py
```
This produces a complete verification report and saves `08_Final\FINAL_SUBMISSION_REPORT.md` (57/57 checks passing).

---

## File Locations & Directory Structure

### Model & Rigging
- Rigged character: `Assets/ChachaAvatar/Models/Chacha_Rigged.fbx`
- Reference export: `08_Final/Chacha_Rigged.fbx`
- Master Blender source: `08_Final/Chacha_Rigged.blend`

### Authentic Voice Library (`Assets/ChachaAvatar/Audio/`)
- `chacha_hi_greeting.wav`: *"Namaste beta, kaise ho?"* (Hindi Greeting)
- `chacha_hi_happy.wav`: *"Wah beta wah, shabash! Bahut badhiya!"* (Hindi Happy)
- `chacha_hi_thinking.wav`: *"Hmm, sochte hain... baat toh gehri hai."* (Hindi Thinking)
- `chacha_hi_surprised.wav`: *"Arre baap re! Yeh kya hua?"* (Hindi Surprised)
- `chacha_hi_nod.wav`: *"Haan haan bilkul, theek hai."* (Hindi Nod / Agreement)
- `chacha_en_greeting.wav`: *"Hello child, blessings to you. How can Chacha help you today?"* (English Greeting)
- `chacha_en_happy.wav`: *"Wonderful! I am very pleased with your progress."* (English Happy)
- `chacha_en_thinking.wav`: *"Hmm, let me ponder this ancient wisdom for a moment..."* (English Thinking)
- `chacha_en_surprised.wav`: *"Goodness gracious! What an extraordinary revelation!"* (English Surprised)

### Avatar Scripts (`Assets/ChachaAvatar/Scripts/`)
- `ChachaAvatarController.cs`: Core avatar controller managing state machine (`Idle`, `Talking`, `Happy`, `Thinking`, `Surprised`), local voice bank, gestures, expressions, and speech playback.
- `ChachaTestUI.cs`: On-screen interactive test GUI for states, gestures, language toggle, and server testing.
- `AudioMouthLipSync.cs`: Lightweight audio amplitude RMS lip-sync driving `Mouth_Open`, with procedural talk flap fallback.
- `AvatarSpeechContracts.cs`: Clean data models (`AvatarCommand`, `VoiceProfile`, `SpeechResult`).
- `HttpBrainApiClient.cs`: HTTP client communicating with `/brain`.
- `HttpSpeechProviders.cs`: HTTP STT and TTS providers communicating with `/stt` and `/tts`.
- `MicrophoneSpeechInput.cs`: Microphone capture utility.
- `ChachaConversationController.cs`: Turn-taking manager (`Idle` -> `Listening` -> `Thinking` -> `Speaking` -> `Idle`).

### Editor Utilities & Materials
- `Assets/ChachaAvatar/Editor/ChachaAvatarSetupWizard.cs`: Automated 1-click setup menu.
- `Assets/ChachaAvatar/Materials/`: 9 Standard materials preserving character design colors (`Chacha_Skin`, `Chacha_Turban_Red`, `Chacha_Moustache_White`, `Chacha_Shirt_White`, `Chacha_Vest_Dark`, `Chacha_Tie_Red`, `Chacha_Pants_Navy`, `Chacha_Shoes_Black`, `Chacha_Cane_Brown`).
- `Assets/ChachaAvatar/Generated/ChachaFloor.mat`: Dark presentation floor material.

---

## Architecture & Integration Details

### Acoustic Formant Voice Synthesis Model
Chacha's voice is synthesized using an acoustic 3-formant vocal tract resonator model designed specifically for an elderly Indian male character:
- Fundamental Pitch $F_0 \approx 110\text{ Hz}$ with natural vibrato ($\Delta f = 1.8\text{ Hz}$, rate $= 5.2\text{ Hz}$).
- Rosenberg glottal excitation pulse with slight vocal fry and subtle breath turbulence ($5\%$).
- Formant frequencies tuned to Indian English and Hindi vowel spaces ($F_1, F_2, F_3$ resonances).
- Pre-rendered clips at 16,000 Hz, 16-bit mono PCM.

### Character Limitations & Notes
- The 3D model's large moustache naturally covers detailed lip geometry. As designed in Phase 3 and Phase 5, the avatar uses `Mouth_Open` for amplitude-based audio synchronization and expressive silhouette changes (`Face_Happy`, `Face_Thinking`, `Face_Surprised`, `Face_SadConfused`).
- The walking stick (cane) is permanently weighted to the right hand, while gestural movements use the left hand, ensuring stable posture during animation.
