# Phase 8 - Local Mock Server

The project now includes a local smoke-test server at `09_LocalMock/chacha_mock_voice_server.py`.

## Purpose

The Unity package already supports the full runtime chain:

`MicrophoneSpeechInput -> STT -> Brain API -> AvatarCommand -> TTS -> AudioMouthLipSync`

Phase 8 adds a no-account way to test that chain. The mock server implements:

| Endpoint | Unity caller | Behavior |
| --- | --- | --- |
| `/stt` | `HttpSpeechToTextProvider` | Accepts multipart audio and returns a canned Hindi or English transcript. |
| `/brain` | `HttpBrainApiClient` | Accepts `{ text, language }` and returns an `AvatarCommand`. |
| `/tts` | `HttpTextToSpeechProvider` | Accepts `{ text, language, voice }` and returns generated WAV audio. |
| `/health` | Browser or PowerShell | Returns a simple service status JSON payload. |

## Result

Unity can now verify endpoint wiring, request/response parsing, `AudioSource` playback, talking animation toggles, and amplitude-based mouth movement before the real backend is available.

The generated audio is intentionally synthetic and is not real speech. It exists only to make runtime integration testable.
