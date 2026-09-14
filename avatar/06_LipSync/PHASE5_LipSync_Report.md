# Phase 5 - Audio-Synchronized Mouth Animation

Chacha uses a runtime, amplitude-based lip-sync system. The generated TTS `AudioClip` is played through one `AudioSource`; `AudioMouthLipSync` samples that exact audio output every frame and drives the exported `Mouth_Open` blendshape.

This is intentionally provider- and language-independent. It works with Hindi and English audio without a paid phoneme/viseme package. The character's large moustache obscures detailed lip geometry, so mouth opening and closing is a clearer and more robust prototype result than a complex phoneme rig.

## Runtime Sequence

`ChachaAvatarController.Speak` applies the requested expression and gesture, requests TTS, sets `IsTalking`, starts lip sync, and begins audio playback. When playback ends or a new command arrives, it stops the audio, resets `IsTalking`, and returns `Mouth_Open` to zero.

## Inspector Tuning

`AudioMouthLipSync` exposes `Sensitivity`, `Silence Threshold`, `Minimum Open Weight`, `Maximum Open Weight`, and `Smoothing`. Start with the defaults. Increase `Sensitivity` only if quiet speech barely opens the mouth; increase `Silence Threshold` if ambient/noise produces unwanted mouth movement.
