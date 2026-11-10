# Ganga AI Mascot — Avatar & Frontend Interface

This directory contains the browser presentation layer and interactive 3D mascot interface for the Ganga AI Mascot (PRJ_316) initiative under Namami Gange (Ministry of Jal Shakti, Government of India).

---

## 1. Overview & Architecture

The frontend interface is a responsive split-screen dashboard providing real-time multimodal interaction with **Chacha Chaudhary**—the official digital guide for Ganga river conservation.

- **Primary Entrypoint**: `index.html`
- **Design System & Styling**: `style.css` (pure white theme `#FFFFFF`, forest-green accents `#15803D`, turquoise Ganga waves `#00A896`, Inter/Outfit typography)
- **3D Mascot Engine**: `mascot.js` (Three.js WebGL engine, 65-bone skeletal rig, procedural breathing, eye blinks, viseme/RMS lip-sync, responsive camera framing)
- **Application Controller**: `app.js` (audio streaming, Web Audio AnalyserNode, state synchronization, verified sources expander, language switching)
- **Multilingual Virtual Keyboard**: `keyboard.js` (on-screen keyboard supporting 12 Indian languages + English with real-time text input)
- **Interactive Educational Quiz**: `quiz.js` & `quiz-data.js` (gamified river conservation questions with instant feedback)
- **Water Quality Reference**: `cpcb-tables.js` (Central Pollution Control Board water classification criteria)

---

## 2. Key UI/UX Improvements Implemented

### A. Pure-White Modern Dashboard
- Pure white background (`#FFFFFF`) with subtle surface cards (`#FAFCFA`) and fine borders (`#E2E8F0`).
- Elegant forest green accents (`#15803D`) and turquoise river waves (`#00A896`).
- Clean, consistent typography hierarchy using `Outfit` for brand titles and `Inter` for interface elements and dialogue.
- Structured vertical left navigation sidebar (Home, Chat, Ganga Resources, Initiatives, Awareness, About, Settings).
- Streamlined top navigation bar with Namami Gange branding, National Emblem, Take Quiz button, and independent Input/Output language dropdowns.

### B. 3D Avatar Stage & Character Framing
- **Full-Body Visibility**: Displays complete Chacha Chaudhary 3D model from turban crest to shoes, including the walking stick.
- **Calibrated Scale & Occupancy**: Model scale calibrated to `1.0` with $91\%$ canvas viewport occupancy, yielding $\approx \mathbf{73.3\%}$ of overall stage height ($\mathbf{+36.8\%}$ larger than baseline).
- **Centering & Ground Contact**: Character vertical midpoint aligned at origin $(0, 0, 0)$ with camera target; shoes rest naturally on contact ground shadow at $y = -0.490$.
- **Non-Occluding Speech Subtitle**: Dedicated speech strip (`.avatar-speech-strip`) sits above the WebGL canvas in flex layout, preventing any overlap over the avatar.
- **Avatar Status Dock**: 4 status pills (Idle, Listening, Thinking, Speaking) with live pulsing indicators reflecting avatar activity.

### C. Conversational Chat Stream
- Stationary 3D avatar panel on the left ($460\text{px}$) with independent scrollable chat stream on the right.
- Message cards with verified sources accordion (`Verified Sources` showing cited PDF reports).
- Custom audio player with real-time waveform visualization driven by Web Audio API `AnalyserNode`.
- Quick-action suggestion pills for instant queries on Namami Gange, water quality, and pollution sources.

### D. Multilingual Interaction & On-Screen Keyboard
- Independent **Input Language** and **Output Language** selectors.
- English configured as default language across all interface elements.
- On-screen virtual keyboard supporting 12 Indic scripts: Hindi, Bengali, Tamil, Telugu, Kannada, Malayalam, Gujarati, Punjabi, Odia, Marathi, Urdu, plus English.
- Smooth toggle switch (`On-Screen Keyboard`) with seamless character injection into the active chat input.

---

## 3. 3D Character & Animation System

- **3D Asset**: `Chacha_New/Chacha_New.glb` (Mixamo-compatible skeletal rig with 28 animations).
- **Procedural Idle Breathing**: Subtle sinusoidal rotation on `mixamorig:Spine1`, `mixamorig:Spine2`, and clavicle bones ensures the character never freezes.
- **Eye Blinking**: Procedural eyelid cycling with randomized intervals ($2.5\text{--}4.5\text{s}$) and natural $120\text{ms}$ blink duration.
- **Real-Time Lip-Sync**:
  - Viseme-driven mouth movement from Rhubarb lip-sync JSON data (visemes: `A`, `B`, `C`, `D`, `E`, `F`, `G`, `H`, `X`).
  - Web Audio AnalyserNode fallback: computes real-time RMS signal levels to drive jaw and mouth opening smoothly at $60\text{fps}$ via LERP interpolation.
- **State Machine**: Transitions across `IDLE`, `LISTENING`, `THINKING`, `SPEAKING`, `GREETING`, `EXPLAINING`, and emotional states.

---

## 4. Files Added and Modified

| File | Status | Description |
| :--- | :--- | :--- |
| `avatar/index.html` | Modified | Complete dashboard layout, header, avatar stage, chat stream, input dock, and modal containers. |
| `avatar/style.css` | Modified | Full pure-white design system, typography, animations, responsive breakpoints, and component styling. |
| `avatar/mascot.js` | Modified | Three.js scene manager, camera calibration ($73.3\%$ stage height), procedural breathing, lip-sync, and state handlers. |
| `avatar/app.js` | Modified | Application controller, Web Audio integration, speech recognition/synthesis coordination, chat message rendering. |
| `avatar/keyboard.js` | Added | Multilingual virtual keyboard with 12 Indian script layouts, key listeners, and caret insertion. |
| `avatar/quiz.js` | Added | Quiz state manager, timer, scoring, and UI event listeners. |
| `avatar/quiz-data.js` | Added | Question bank on Ganga river, conservation programs, and water quality criteria. |
| `avatar/cpcb-tables.js` | Added | Central Pollution Control Board (CPCB) designated best-use water quality classification tables. |
| `avatar/avatar3d.html` | Modified | Standalone 3D avatar viewport for isolated model inspection and calibration. |
| `avatar/tests/*.test.js`| Added | Automated unit tests for quiz logic and CPCB table lookups. |

---

## 5. Verification & Testing

- **Automated Test Suite**: All 7 integration test suites passing ($100\%$):
  1. HTML Structure & element integrity.
  2. Default English language configuration.
  3. CSS cache-buster and stylesheet integrity.
  4. 3D Mascot animation & lip-sync pipeline.
  5. Frontend app event binding & audio hooks.
  6. English RAG & Rhubarb lip-sync endpoint.
  7. Hindi RAG & Neural Voice pipeline.
- **Cross-Browser Verification**: Verified in Microsoft Edge and Google Chrome via Headless/CDP rendering with zero WebGL errors.

---

## 6. Scope Boundaries & Preserved Modules

- **Unchanged**: RAG engine, SQLite vector storage, ONNX embeddings, Groq/OpenRouter generation, Edge TTS, Vosk STT models, and CPCB live station polling.
- **Next Steps / Planned Future Work**:
  - Expanded native morph targets for higher-fidelity viseme mouth blendshapes.
  - Full mobile viewport optimizations for screens $< 640\text{px}$.
  - Offline PWA caching for standalone deployment.
