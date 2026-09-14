# Phase 3 - Facial Expression System

The supplied Chacha mesh has no facial controls or existing blendshapes. The rig generator therefore creates Unity-compatible shape keys directly on the preserved character mesh:

| Shape key | Avatar use |
| --- | --- |
| `Face_Happy` | Positive response, used with `Happy_Reaction`. |
| `Face_Thinking` | Reflective response, used with `Thinking_Reaction`. |
| `Face_Surprised` | Attention or surprise. |
| `Face_SadConfused` | Uncertain or sympathetic response. |
| `Mouth_Open` | Audio-driven mouth opening for the Phase 5 lip-sync system. |

`Basis` is the neutral face. Unity should set only one expression key at a time, normally in the 0.0 to 1.0 range, and blend `Mouth_Open` independently while the avatar is speaking.

The character's moustache covers detailed lip geometry, so this system deliberately provides strong, readable silhouette changes rather than attempting full phoneme-specific facial reconstruction. It is appropriate for a lightweight student-project conversational avatar.
