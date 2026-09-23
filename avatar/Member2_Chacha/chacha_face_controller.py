"""
Chacha Chaudhary - Digital Avatar Facial Controller
Stage 9: Facial Animation Controller & Blending System

Provides high-level, decoupled control over:
- 7 Composite Emotions (Happy, Sad, Angry, Surprised, Confused, Thinking, Laughing, Neutral)
- 16 Speech Visemes (A, E, I, O, U, MBP, FV, L, DTN, KG, SHCH, R, S, NG, Th, Silence)
- 11 Modular Controls (Blinks, Brows, Eyes, Mouth, Jaw)
"""

import bpy

class ChachaFaceController:
    # Supported emotion names mapping to shape key names
    EMOTIONS = {
        "neutral": None,
        "happy": "Emotion_Happy",
        "sad": "Emotion_Sad",
        "angry": "Emotion_Angry",
        "surprised": "Emotion_Surprised",
        "confused": "Emotion_Confused",
        "thinking": "Emotion_Thinking",
        "laughing": "Emotion_Laughing"
    }

    # Supported viseme names mapping to shape key names
    VISEMES = {
        "a": "Viseme_A",
        "e": "Viseme_E",
        "i": "Viseme_I",
        "o": "Viseme_O",
        "u": "Viseme_U",
        "mbp": "Viseme_MBP",
        "fv": "Viseme_FV",
        "l": "Viseme_L",
        "dtn": "Viseme_DTN",
        "kg": "Viseme_KG",
        "shch": "Viseme_SHCH",
        "r": "Viseme_R",
        "s": "Viseme_S",
        "ng": "Viseme_NG",
        "th": "Viseme_Th",
        "silence": "Viseme_Silence"
    }

    # Modular controls
    MODULAR_KEYS = [
        "Blink_L", "Blink_R", "Brow_Raise", "Brow_Furrow",
        "Eyes_Squint", "Eyes_Wide", "Mouth_Smile", "Mouth_Frown",
        "Mouth_Open", "Mouth_O", "Jaw_Drop"
    ]

    def __init__(self, mesh_name="model"):
        self.mesh_name = mesh_name
        self.mesh_obj = bpy.data.objects.get(mesh_name)
        if not self.mesh_obj or not self.mesh_obj.data.shape_keys:
            raise RuntimeError(f"Mesh '{mesh_name}' or its Shape Keys could not be found.")
        self.key_blocks = self.mesh_obj.data.shape_keys.key_blocks
        self.current_emotion = "neutral"
        self.current_emotion_intensity = 0.0
        self.current_viseme = "silence"
        self.current_viseme_intensity = 0.0

    def update_view(self):
        """Forces Blender viewport/depsgraph to update."""
        bpy.context.view_layer.update()

    def set_emotion(self, emotion_name, intensity=1.0):
        """
        Sets the primary facial emotion with continuous intensity (0.0 to 1.0).
        Automatically clears other composite emotions to prevent conflicting facial states.
        """
        emo_key = emotion_name.strip().lower()
        if emo_key not in self.EMOTIONS:
            raise ValueError(f"Unknown emotion '{emotion_name}'. Supported: {list(self.EMOTIONS.keys())}")

        intensity = max(0.0, min(1.0, float(intensity)))

        # Clear all composite emotion keys
        for name, sk_name in self.EMOTIONS.items():
            if sk_name and sk_name in self.key_blocks:
                self.key_blocks[sk_name].value = 0.0

        # Activate target emotion if not neutral
        target_sk = self.EMOTIONS[emo_key]
        if target_sk and target_sk in self.key_blocks:
            self.key_blocks[target_sk].value = intensity
            self.current_emotion = emo_key
            self.current_emotion_intensity = intensity
        else:
            self.current_emotion = "neutral"
            self.current_emotion_intensity = 0.0

        self.update_view()

    def clear_emotion(self):
        """Resets all composite emotions to neutral (0.0)."""
        self.set_emotion("neutral", 0.0)

    def set_viseme(self, viseme_name, intensity=1.0):
        """
        Sets the active speech viseme with intensity (0.0 to 1.0).
        Enforces mutual exclusion among speech visemes.
        """
        vis_key = viseme_name.strip().lower()
        if vis_key not in self.VISEMES:
            raise ValueError(f"Unknown viseme '{viseme_name}'. Supported: {list(self.VISEMES.keys())}")

        intensity = max(0.0, min(1.0, float(intensity)))

        # Clear all viseme keys
        for name, sk_name in self.VISEMES.items():
            if sk_name in self.key_blocks:
                self.key_blocks[sk_name].value = 0.0

        # Activate target viseme
        target_sk = self.VISEMES[vis_key]
        if target_sk in self.key_blocks:
            self.key_blocks[target_sk].value = intensity
            self.current_viseme = vis_key
            self.current_viseme_intensity = intensity

        self.update_view()

    def transition_viseme(self, from_viseme, to_viseme, factor, intensity=1.0):
        """
        Smoothly interpolates between two visemes (factor from 0.0 to 1.0).
        Clears all other visemes.
        """
        k1 = from_viseme.strip().lower()
        k2 = to_viseme.strip().lower()
        if k1 not in self.VISEMES or k2 not in self.VISEMES:
            raise ValueError("Invalid viseme in transition.")

        factor = max(0.0, min(1.0, float(factor)))
        intensity = max(0.0, min(1.0, float(intensity)))

        # Clear all visemes
        for name, sk_name in self.VISEMES.items():
            if sk_name in self.key_blocks:
                self.key_blocks[sk_name].value = 0.0

        # Blend
        sk1 = self.VISEMES[k1]
        sk2 = self.VISEMES[k2]
        if sk1 in self.key_blocks:
            self.key_blocks[sk1].value = (1.0 - factor) * intensity
        if sk2 in self.key_blocks:
            self.key_blocks[sk2].value = factor * intensity

        self.update_view()

    def clear_viseme(self):
        """Resets all speech visemes to 0.0."""
        for name, sk_name in self.VISEMES.items():
            if sk_name in self.key_blocks:
                self.key_blocks[sk_name].value = 0.0
        self.current_viseme = "silence"
        self.current_viseme_intensity = 0.0
        self.update_view()

    def set_blink(self, side="both", intensity=1.0):
        """Controls eyelid blinking: 'left', 'right', or 'both'."""
        side = side.strip().lower()
        intensity = max(0.0, min(1.0, float(intensity)))

        if side in ["left", "l"]:
            self.key_blocks["Blink_L"].value = intensity
        elif side in ["right", "r"]:
            self.key_blocks["Blink_R"].value = intensity
        elif side in ["both", "all"]:
            self.key_blocks["Blink_L"].value = intensity
            self.key_blocks["Blink_R"].value = intensity
        else:
            raise ValueError(f"Unknown blink side '{side}'. Use 'left', 'right', or 'both'.")

        self.update_view()

    def set_modular(self, param_name, value):
        """Sets any modular shape key directly (0.0 to 1.0)."""
        if param_name in self.key_blocks:
            self.key_blocks[param_name].value = max(0.0, min(1.0, float(value)))
            self.update_view()
        else:
            raise KeyError(f"Shape key '{param_name}' not found.")

    def reset_face(self):
        """Resets ALL 34 non-Basis shape keys to exactly 0.0 (neutral rest pose)."""
        for sk in self.key_blocks:
            if sk.name != "Basis":
                sk.value = 0.0
        self.current_emotion = "neutral"
        self.current_emotion_intensity = 0.0
        self.current_viseme = "silence"
        self.current_viseme_intensity = 0.0
        self.update_view()

    def get_state(self):
        """Returns dictionary of currently active (non-zero) shape keys."""
        state = {}
        for sk in self.key_blocks:
            if sk.name != "Basis" and sk.value > 0.001:
                state[sk.name] = round(sk.value, 4)
        return {
            "current_emotion": self.current_emotion,
            "current_emotion_intensity": self.current_emotion_intensity,
            "current_viseme": self.current_viseme,
            "current_viseme_intensity": self.current_viseme_intensity,
            "active_shape_keys": state
        }
