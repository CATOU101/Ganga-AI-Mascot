# Phase 4 - Chacha Digital Voice & TTS Synthesis System

Date: 2026-09-12

## Acoustic Character Profile

- **Persona**: Chacha (warm, respectable, encouraging elderly Indian uncle)
- **Fundamental Pitch (F0)**: 105 Hz – 120 Hz (mature male chest register)
- **Vocal Tract Resonance**: 3-formant digital resonator modeled after adult male Hindi/English articulation
- **Vocal Inflection**: Warm 4.8 Hz flutter vibrato, intonational sentence-final cadence
- **Format**: Standard 16 kHz 16-bit Mono PCM WAV (100% offline, zero-paid API dependencies)

## Voice Library Manifest

| File | Character Dialogue | Pitch | Duration |
|---|---|:---:|:---:|
| `chacha_hi_greeting.wav` | "Namaste beta! Main taiyar hoon. Aaj hum kya seekhenge?" | 110.0 Hz | 4.76s |
| `chacha_hi_thinking.wav` | "Hmm, sochne do beta... Achha sawaal hai." | 108.0 Hz | 4.18s |
| `chacha_hi_happy.wav` | "Wah beta wah! Yeh toh bahut hi badhiya kaam kiya tumne!" | 116.0 Hz | 4.86s |
| `chacha_hi_surprised.wav` | "Arre baap re! Sach mein? Yeh toh kamaal ho gaya!" | 120.0 Hz | 4.32s |
| `chacha_hi_nod.wav` | "Haan beta, bilkul sahi baat hai. Main samajh gaya." | 108.0 Hz | 4.39s |
| `chacha_en_greeting.wav` | "Hello my child! Chacha is here to guide and help you." | 112.0 Hz | 4.47s |
| `chacha_en_thinking.wav` | "Let me ponder this for a moment... An interesting thought." | 110.0 Hz | 4.96s |
| `chacha_en_happy.wav` | "Wonderful news! Keep up the brilliant work." | 118.0 Hz | 3.26s |
| `chacha_en_surprised.wav` | "Good heavens! That is truly remarkable!" | 122.0 Hz | 3.22s |

## Integration Architecture

1. **Mock Voice Server (`09_LocalMock`)**: When requested for speech, the server matches key phrases from this library or dynamically synthesizes vocal formant speech on the fly.
2. **Unity Audio (`Assets/ChachaAvatar/Audio/`)**: All clips are imported with AudioImporter settings and mapped into the avatar runtime for instant offline and mock server playback.
3. **Lip-Sync (`AudioMouthLipSync`)**: Audio amplitude envelope samples the formant energy peaks to flap `Mouth_Open` synchronously with spoken vowels.
