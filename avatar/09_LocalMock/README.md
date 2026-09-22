# Chacha Local Mock Voice Server

This folder contains a no-dependency local HTTP server for testing the Unity avatar flow before real STT, Brain, or TTS services are available.

## Run

From the repository root:

```powershell
python 09_LocalMock\chacha_mock_voice_server.py --host 127.0.0.1 --port 8765
```

Open `http://127.0.0.1:8765/health` to confirm it is running.

## Unity Endpoints

Set these fields on the generated `ChachaAvatar.prefab`:

| Unity component | Field | Value |
| --- | --- | --- |
| `HttpSpeechToTextProvider` | `Endpoint` | `http://127.0.0.1:8765/stt` |
| `HttpBrainApiClient` | `Endpoint` | `http://127.0.0.1:8765/brain` |
| Hindi `VoiceProfile` | `Tts Endpoint` | `http://127.0.0.1:8765/tts` |
| English `VoiceProfile` | `Tts Endpoint` | `http://127.0.0.1:8765/tts` |

The mock STT endpoint ignores the microphone audio and returns a canned user phrase. The mock Brain endpoint returns an `AvatarCommand`. The mock TTS endpoint returns a short generated WAV tone so Unity can verify audio playback and `Mouth_Open` lip-sync behavior.

## Quick Checks

```powershell
Invoke-RestMethod http://127.0.0.1:8765/health
Invoke-RestMethod -Method Post http://127.0.0.1:8765/brain -ContentType application/json -Body '{"text":"Namaste","language":"hi"}'
```

Use this only as a smoke-test harness. Replace the endpoints with real providers once Member 1's backend is ready.
