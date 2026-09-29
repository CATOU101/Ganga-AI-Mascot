# Phase 7 - Unity-Ready Avatar Setup

`07_Unity` is a Unity 2021.3+ project starter. The validated rigged character is already included at `Assets/ChachaAvatar/Models/Chacha_Rigged.fbx`.

## One-Time Import

1. Open `07_Unity` using Unity Hub 2021.3 or later.
2. Select `Assets/ChachaAvatar/Models/Chacha_Rigged.fbx` in Unity's Project window. On the Rig tab choose `Humanoid`, then click Apply. On the Animation tab, import the listed clips.
3. Run `Chacha > Create Unity-Ready Avatar From Selected FBX`.

The setup wizard creates these assets in `Assets/ChachaAvatar/Generated/`:

| Asset | Purpose |
| --- | --- |
| `ChachaAvatar.prefab` | Avatar, audio, STT, TTS, Brain, conversation, and lip-sync components already connected. |
| `ChachaAnimator.controller` | Idle, talking, and one-shot gesture/reaction states. |
| `ChachaDemo.unity` | Camera, lighting, presentation floor, and the generated avatar prefab. |

## Animator Architecture

The default state is `Idle_Breathing`. `IsTalking` switches between `Idle_Breathing` and `Talking_UpperBody`. Trigger parameters select `Simple_Hand_Gesture`, `Head_Nod`, `Head_Turn`, `Happy_Reaction`, and `Thinking_Reaction`; each returns to idle after its clip completes.

Set the STT, TTS, and Brain endpoint fields on the generated prefab. Create UI press/release events calling `ChachaConversationController.BeginListening` and `EndListening`.

Run `Chacha > Create Demo Scene` after the prefab has been created. It opens and saves `ChachaDemo.unity`, framing Chacha from the front with a neutral presentation environment.

## Verification Checklist

- The FBX Inspector lists seven animation clips and six blendshapes, including `Mouth_Open`.
- The generated prefab has an Animator, AudioSource, ChachaAvatarController, ChachaConversationController, AudioMouthLipSync, HttpTextToSpeechProvider, HttpSpeechToTextProvider, and HttpBrainApiClient.
- A Brain response with `language` set to `hi` or `en` selects the matching voice profile.
