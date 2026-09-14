# Phase 6 - Brain API Integration

The Unity package now provides a complete, backend-neutral conversation path:

`MicrophoneSpeechInput -> SpeechToTextProvider -> BrainApiClient -> ChachaAvatarController -> TextToSpeechProvider -> AudioMouthLipSync`

`ChachaConversationController` owns the four runtime states: `Idle`, `Listening`, `Thinking`, and `Speaking`. It prevents overlapping microphone requests and returns to `Idle` after successful speech, STT failure, Brain failure, or TTS failure.

## Member 1 Contract

The configured Brain endpoint receives a JSON POST body:

```json
{"text":"Namaste Chacha","language":"hi"}
```

It must return JSON matching `AvatarCommand`:

```json
{"text":"Namaste beta! Kaise ho?","language":"hi","emotion":"happy","gesture":"wave"}
```

Accepted gesture values are `wave`, `hand`, `gesture`, `nod`, `turn`, `happy`, and `thinking`. Accepted expression values are `neutral`, `happy`, `thinking`, `surprised`, `sad`, `confused`, and `sad_confused`.

`HttpBrainApiClient` also has an optional `Authorization` Inspector field for a standard authorization header. Replace this component rather than changing avatar code if the backend later uses WebSockets, authentication refresh, or a different request format.
