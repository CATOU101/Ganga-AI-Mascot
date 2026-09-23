"""
Chacha Chaudhary - Digital Avatar Runtime Behavior & State Controller
Stage 11: Natural Idle, Automatic Blinking, and Avatar State Behavior

Coordinates the high-level avatar autonomy stack:
    BODY (Mixamo Skeletal Actions)
    + EMOTION (Composite Facial Expressions)
    + LIP-SYNC (Phonetic Speech Articulation)
    + BLINK (Procedural & Manual Eyelid Dynamics)

Maintains deterministic state machine:
    IDLE <-> LISTENING <-> THINKING <-> SPEAKING (with EMOTING support)
"""

import os
import sys
import math
import random
import bpy

# Set up module search path
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

from chacha_face_controller import ChachaFaceController
from chacha_lipsync_player import ChachaLipSyncPlayer


class AvatarState:
    """Supported high-level avatar behavioral states."""
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"


class BlinkConfig:
    """Configurable timing parameters for procedural automatic blinking."""
    def __init__(self, min_interval=3.0, max_interval=7.0, blink_duration=0.15):
        self.min_interval = float(min_interval)
        self.max_interval = float(max_interval)
        self.blink_duration = float(blink_duration)


class ListeningConfig:
    """Configurable subtle attentive facial offsets for LISTENING state."""
    def __init__(self, brow_raise=0.20, eyes_wide=0.15):
        self.brow_raise = float(brow_raise)
        self.eyes_wide = float(eyes_wide)


class ThinkingConfig:
    """Configurable parameters for THINKING state."""
    def __init__(self, emotion_intensity=0.75, body_action="Chacha_Thinking"):
        self.emotion_intensity = float(emotion_intensity)
        self.body_action = body_action


class BlinkEngine:
    """
    Procedural & Manual Eyelid Blink Engine.
    
    Generates natural, non-periodic bilateral blinks using smooth sinusoidal motion curves.
    Supports deterministic seeding for test repeatability and instantaneous manual overrides.
    """

    def __init__(self, face_controller: ChachaFaceController, config: BlinkConfig = None, seed: int = None):
        self.face_controller = face_controller
        self.config = config or BlinkConfig()
        self.rng = random.Random(seed)

        # Procedural state
        self.is_blinking = False
        self.blink_side = "both"  # "both", "left", "right"
        self.blink_progress = 0.0  # 0.0 to blink_duration
        self.current_duration = self.config.blink_duration
        self.time_to_next_blink = self._sample_interval()
        self.is_manual = False

    def seed(self, seed_val: int):
        """Seeds the internal PRNG for deterministic testing."""
        self.rng = random.Random(seed_val)
        self.time_to_next_blink = self._sample_interval()

    def _sample_interval(self) -> float:
        """Draws next blink interval uniformly between min_interval and max_interval."""
        return self.rng.uniform(self.config.min_interval, self.config.max_interval)

    def trigger_manual_blink(self, side: str = "both", duration: float = None):
        """
        Immediately triggers a manual blink, preempting any pending procedural timer.
        
        Args:
            side: 'both', 'left', or 'right'.
            duration: Optional duration override (default: config.blink_duration).
        """
        self.is_blinking = True
        self.is_manual = True
        self.blink_side = side.lower().strip()
        self.blink_progress = 0.0
        self.current_duration = float(duration) if duration is not None else self.config.blink_duration

    def update(self, dt: float):
        """
        Advances blink engine by dt seconds.
        
        Calculates eyelid position via sinusoidal bell curve:
            intensity = sin(pi * progress / duration)
        """
        if dt <= 0:
            return

        if self.is_blinking:
            self.blink_progress += dt
            if self.blink_progress >= self.current_duration:
                # Blink cycle finished
                self.face_controller.set_blink(self.blink_side, 0.0)
                self.is_blinking = False
                self.is_manual = False
                self.blink_progress = 0.0
                self.time_to_next_blink = self._sample_interval()
            else:
                p = self.blink_progress / self.current_duration
                # Smooth sinusoidal curve: 0 -> 1 -> 0
                val = math.sin(math.pi * p)
                self.face_controller.set_blink(self.blink_side, val)
        else:
            self.time_to_next_blink -= dt
            if self.time_to_next_blink <= 0.0:
                # Start procedural automatic blink
                self.is_blinking = True
                self.is_manual = False
                self.blink_side = "both"
                self.blink_progress = 0.0
                self.current_duration = self.config.blink_duration


class ChachaAvatarController:
    """
    Master Avatar Runtime Controller.
    
    Orchestrates skeletal body actions, facial emotions, modular expressions,
    procedural blinking, and phonetic lip-sync.
    """

    def __init__(self, mesh_name: str = "model", armature_name: str = "Armature"):
        self.mesh_name = mesh_name
        self.armature_name = armature_name

        # Resolve Blender objects
        self.mesh_obj = bpy.data.objects.get(mesh_name)
        self.armature_obj = bpy.data.objects.get(armature_name)
        if not self.armature_obj:
            # Fallback to first armature in scene
            arms = [o for o in bpy.data.objects if o.type == 'ARMATURE']
            self.armature_obj = arms[0] if arms else None

        if not self.mesh_obj or not self.mesh_obj.data.shape_keys:
            raise RuntimeError(f"Mesh '{mesh_name}' or Shape Keys not found.")

        # Subsystems
        self.face_controller = ChachaFaceController(mesh_name=mesh_name)
        self.lipsync_player = ChachaLipSyncPlayer(face_controller=self.face_controller, mesh_name=mesh_name)
        self.blink_config = BlinkConfig()
        self.listening_config = ListeningConfig()
        self.thinking_config = ThinkingConfig()
        self.blink_engine = BlinkEngine(face_controller=self.face_controller, config=self.blink_config)

        # State tracking
        self.state = AvatarState.IDLE
        self.current_body_action = "Chacha_Idle"
        self.active_emotion = "neutral"
        self.active_emotion_intensity = 0.0
        self.is_lipsync_active = False
        self.lipsync_elapsed = 0.0
        self._frame_handler = None

        # Initialize to clean IDLE state
        self._apply_body_action("Chacha_Idle")

    # -------------------------------------------------------------------------
    # State Management & Priority Arbitration
    # -------------------------------------------------------------------------
    def set_state(self, new_state: str):
        """
        Transitions the avatar into a new behavioral state.
        
        Args:
            new_state: 'idle', 'listening', 'thinking', or 'speaking'.
        """
        state_key = str(new_state).lower().strip()
        if state_key not in [AvatarState.IDLE, AvatarState.LISTENING, AvatarState.THINKING, AvatarState.SPEAKING]:
            raise ValueError(f"Unknown avatar state '{new_state}'. Allowed: idle, listening, thinking, speaking")

        prev_state = self.state
        self.state = state_key

        # Clear state-specific facial adjustments from previous state
        if prev_state == AvatarState.LISTENING:
            self._clear_listening_posture()
        elif prev_state == AvatarState.THINKING:
            # If leaving thinking, clear automatic thinking emotion unless user explicitly requested thinking
            if self.face_controller.current_emotion == "thinking" and self.active_emotion != "thinking":
                self.face_controller.clear_emotion()
                # Re-apply user's base emotion if one was set prior
                if self.active_emotion != "neutral":
                    self.face_controller.set_emotion(self.active_emotion, self.active_emotion_intensity)

        # Apply target state configurations
        if self.state == AvatarState.IDLE:
            self._apply_body_action("Chacha_Idle")
            if self.face_controller.current_emotion == "thinking" and self.active_emotion != "thinking":
                self.face_controller.clear_emotion()
                if self.active_emotion != "neutral":
                    self.face_controller.set_emotion(self.active_emotion, self.active_emotion_intensity)
            if self.is_lipsync_active:
                self.stop_lipsync()

        elif self.state == AvatarState.LISTENING:
            self._apply_body_action("Chacha_Idle")
            self._apply_listening_posture()
            if self.is_lipsync_active:
                self.stop_lipsync()

        elif self.state == AvatarState.THINKING:
            self._apply_body_action(self.thinking_config.body_action)
            self.face_controller.set_emotion("thinking", self.thinking_config.emotion_intensity)
            if self.is_lipsync_active:
                self.stop_lipsync()

        elif self.state == AvatarState.SPEAKING:
            # Default to Idle body motion unless already performing an explicit gesture
            if self.current_body_action not in bpy.data.actions:
                self._apply_body_action("Chacha_Idle")

    def get_state(self) -> dict:
        """Returns comprehensive dictionary of current avatar runtime state."""
        return {
            "state": self.state,
            "body_action": self.current_body_action,
            "active_emotion": self.active_emotion,
            "active_emotion_intensity": self.active_emotion_intensity,
            "facial_controller_emotion": self.face_controller.current_emotion,
            "is_lipsync_active": self.is_lipsync_active,
            "lipsync_elapsed": round(self.lipsync_elapsed, 4),
            "is_blinking": self.blink_engine.is_blinking,
            "active_visemes": self.lipsync_player.get_active_visemes()
        }

    # -------------------------------------------------------------------------
    # Body Action Handling
    # -------------------------------------------------------------------------
    def _apply_body_action(self, action_name: str):
        """Assigns an existing Mixamo action to the Armature without modifying it."""
        if not self.armature_obj:
            return
        act = bpy.data.actions.get(action_name)
        if not act:
            raise KeyError(f"Body action '{action_name}' not found in bpy.data.actions")

        if not self.armature_obj.animation_data:
            self.armature_obj.animation_data_create()
        self.armature_obj.animation_data.action = act
        self.current_body_action = action_name

    def play_body_action(self, action_name: str):
        """
        Explicitly triggers a body gesture action (e.g. 'Chacha_Nod', 'Chacha_Waving').
        Does NOT alter or reset active facial emotions, lip-sync, or blinks.
        """
        self._apply_body_action(action_name)

    # -------------------------------------------------------------------------
    # Facial Emotion Handling
    # -------------------------------------------------------------------------
    def set_emotion(self, emotion_name: str, intensity: float = 1.0):
        """
        Sets the primary facial emotion without affecting body motion or blinking.
        """
        emo_key = emotion_name.lower().strip()
        intensity = max(0.0, min(1.0, float(intensity)))
        self.active_emotion = emo_key
        self.active_emotion_intensity = intensity
        self.face_controller.set_emotion(emo_key, intensity)

    def clear_emotion(self):
        """Clears facial emotion to neutral without modifying body state or blinks."""
        self.active_emotion = "neutral"
        self.active_emotion_intensity = 0.0
        self.face_controller.clear_emotion()

    # -------------------------------------------------------------------------
    # Listening Posture
    # -------------------------------------------------------------------------
    def _apply_listening_posture(self):
        """Applies subtle attentive micro-expressions for LISTENING state."""
        self.face_controller.set_modular("Brow_Raise", self.listening_config.brow_raise)
        self.face_controller.set_modular("Eyes_Wide", self.listening_config.eyes_wide)

    def _clear_listening_posture(self):
        """Restores attentive modular shape keys to 0.0."""
        self.face_controller.set_modular("Brow_Raise", 0.0)
        self.face_controller.set_modular("Eyes_Wide", 0.0)

    # -------------------------------------------------------------------------
    # Lip-Sync Playback
    # -------------------------------------------------------------------------
    def start_lipsync(self, json_path: str, start_time: float = 0.0):
        """
        Loads a LipSync JSON and enters SPEAKING state.
        
        Args:
            json_path: Path to the JSON timeline.
            start_time: Time offset in seconds (default: 0.0).
        """
        self.lipsync_player.load(json_path, validate_audio=False)
        self.is_lipsync_active = True
        self.lipsync_elapsed = float(start_time)
        self.set_state(AvatarState.SPEAKING)
        self.lipsync_player.update(self.lipsync_elapsed)

    def stop_lipsync(self):
        """Stops lip-sync playback, clears speech visemes, and returns to IDLE if speaking."""
        self.is_lipsync_active = False
        self.lipsync_elapsed = 0.0
        self.lipsync_player.reset()
        if self.state == AvatarState.SPEAKING:
            self.set_state(AvatarState.IDLE)

    # -------------------------------------------------------------------------
    # Manual & Automatic Blinking API
    # -------------------------------------------------------------------------
    def blink(self, duration: float = None):
        """Immediately executes an instantaneous bilateral blink."""
        self.blink_engine.trigger_manual_blink(side="both", duration=duration)

    def blink_both(self, duration: float = None):
        """Alias for blink()."""
        self.blink(duration=duration)

    def blink_left(self, duration: float = None):
        """Immediately executes an instantaneous left-eye blink."""
        self.blink_engine.trigger_manual_blink(side="left", duration=duration)

    def blink_right(self, duration: float = None):
        """Immediately executes an instantaneous right-eye blink."""
        self.blink_engine.trigger_manual_blink(side="right", duration=duration)

    # -------------------------------------------------------------------------
    # Explicit Reset API
    # -------------------------------------------------------------------------
    def reset_lipsync(self):
        """Resets ONLY speech visemes to 0.0, leaving emotion, blinks, and body intact."""
        self.lipsync_player.reset()
        self.is_lipsync_active = False
        self.lipsync_elapsed = 0.0

    def reset_face(self):
        """Resets ALL facial shape keys (emotions, modular keys, blinks) to 0.0."""
        self.face_controller.reset_face()
        self.active_emotion = "neutral"
        self.active_emotion_intensity = 0.0

    def reset_full(self):
        """Resets the entire avatar runtime state to baseline clean IDLE."""
        self.stop_lipsync()
        self.reset_face()
        self.set_state(AvatarState.IDLE)
        self._apply_body_action("Chacha_Idle")
        if self.armature_obj:
            bpy.context.scene.frame_set(1)

    def reset(self):
        """Clean alias for reset_full()."""
        self.reset_full()

    # -------------------------------------------------------------------------
    # Runtime Clocks & Timeline Integration
    # -------------------------------------------------------------------------
    def update(self, dt: float):
        """
        Advances avatar runtime state by dt seconds.
        
        Updates:
            1. Procedural and manual blinking.
            2. Lip-sync playback if currently speaking.
        """
        if dt <= 0:
            return

        # 1. Update blinking
        self.blink_engine.update(dt)

        # 2. Update lip-sync playback
        if self.is_lipsync_active:
            self.lipsync_elapsed += dt
            if self.lipsync_elapsed >= self.lipsync_player.duration_seconds:
                # Speech completed: gracefully stop and return to IDLE
                self.stop_lipsync()
            else:
                self.lipsync_player.update(self.lipsync_elapsed)

    def update_frame(self, frame: float, start_frame: int = 1, fps: float = None):
        """
        Updates avatar state based on a Blender timeline frame.
        """
        if fps is None:
            fps = self.lipsync_player.get_scene_fps()
        rel_t = max(0.0, (frame - start_frame) / fps)
        # Advance blink engine
        dt = 1.0 / fps
        self.update(dt)

    def attach_to_scene(self, start_frame: int = 1):
        """
        Attaches a post frame-change handler to Blender's timeline
        so playback (Alt+A / Spacebar) updates the avatar automatically.
        """
        self.detach_from_scene()
        last_frame = [bpy.context.scene.frame_current]

        def _avatar_frame_callback(scene):
            cur_frame = scene.frame_current
            fps = self.lipsync_player.get_scene_fps()
            delta_frames = cur_frame - last_frame[0]
            dt = abs(delta_frames) / fps if delta_frames != 0 else (1.0 / fps)
            last_frame[0] = cur_frame
            self.update(dt)

        self._frame_handler = _avatar_frame_callback
        bpy.app.handlers.frame_change_post.append(self._frame_handler)

    def detach_from_scene(self):
        """Removes the frame-change handler cleanly."""
        if self._frame_handler and self._frame_handler in bpy.app.handlers.frame_change_post:
            bpy.app.handlers.frame_change_post.remove(self._frame_handler)
        self._frame_handler = None
