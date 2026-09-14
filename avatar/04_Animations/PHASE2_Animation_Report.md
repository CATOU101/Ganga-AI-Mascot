# Phase 2 - Reusable Animation Clips

All clips are authored on `Chacha_Humanoid_Armature` at 24 frames per second and are exported with `Chacha_Rigged.fbx` as individual animation takes.

| Clip | Frames | Use in Unity |
| --- | ---: | --- |
| `Idle_Breathing` | 1-60 | Loop while waiting or listening. |
| `Talking_UpperBody` | 1-72 | Loop during speech playback; mouth movement is added in Phase 5. |
| `Head_Nod` | 1-48 | One-shot acknowledgement. |
| `Head_Turn` | 1-60 | One-shot attention shift, then return to the camera. |
| `Simple_Hand_Gesture` | 1-72 | One-shot conversational hand movement. |
| `Happy_Reaction` | 1-60 | One-shot positive response. |
| `Thinking_Reaction` | 1-60 | One-shot reflective response. |

The cane is weighted to the right hand and is intentionally not animated by the left-hand gesture clips. The actions use gentle upper-body rotations only; this keeps the animation lightweight and avoids visible leg or cane instability on the auto-weighted character.

## Unity Setup

In Unity's FBX importer, set Rig to `Humanoid` and Animation to import the takes. Enable looping only for `Idle_Breathing` and `Talking_UpperBody`. The remaining clips should be non-looping triggers from the avatar animator.
