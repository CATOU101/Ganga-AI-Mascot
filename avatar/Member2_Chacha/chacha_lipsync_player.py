"""
Chacha Chaudhary - Digital Avatar Lip-Sync Playback Integration
Stage 10C: Blender Lip-Sync Playback System

Consumes phonetic viseme timelines generated in Stage 10B (Output/LipSync/*.json)
and drives the 16 speech Viseme Shape Keys via ChachaFaceController.

Architecture:
    BODY (Mixamo Skeletal Actions)
    + EMOTION (Composite Facial Emotions)
    + LIP-SYNC (Phonetic Speech Visemes)
    + BLINK (Eyelid Controls)
All layers remain completely decoupled and operate simultaneously.
"""

import os
import sys
import json
import wave
import math
import bpy

# Ensure local module directory is in sys.path
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

from chacha_face_controller import ChachaFaceController


class LipSyncError(Exception):
    """Base exception for lip-sync playback errors."""
    pass


class LipSyncDurationMismatchError(LipSyncError):
    """Raised when audio file duration does not match JSON duration."""
    pass


class ChachaLipSyncPlayer:
    """
    Deterministic Blender-side Lip-Sync Playback Controller.
    
    Drives the 16 speech visemes on the Chacha model from structured LipSync JSON data
    without altering body Actions, composite emotions, blinks, or mesh topology.
    """

    def __init__(self, face_controller=None, mesh_name="model", mapping_config_path=None):
        """
        Initializes the LipSync Player.
        
        Args:
            face_controller: Optional existing instance of ChachaFaceController.
            mesh_name: Target mesh object name (default: "model").
            mapping_config_path: Path to viseme_mapping.json (uses existing mapping config).
        """
        self.mesh_name = mesh_name
        self.face_controller = face_controller or ChachaFaceController(mesh_name=mesh_name)

        # Load existing mapping configuration to avoid duplicating mappings
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = mapping_config_path or os.path.join(base_dir, "viseme_mapping.json")
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Viseme mapping configuration not found: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            self.mapping_config = json.load(f)

        self.allowed_visemes = set(self.mapping_config.get("chacha_allowed_visemes", []))

        # Runtime playback state
        self.json_path = None
        self.data = None
        self.audio_file = None
        self.language = "en"
        self.duration_seconds = 0.0
        self.transition_ms = 50.0  # default 50ms smoothing window
        self.transition_seconds = 0.05
        self.visemes = []  # list of sorted segment dicts
        self.is_playing = False
        self.start_frame = 1
        self._frame_handler = None

    def get_scene_fps(self) -> float:
        """
        Retrieves the active Blender scene frame rate dynamically.
        DOES NOT assume 24 FPS; handles custom FPS and fractional fps_base.
        """
        scene = bpy.context.scene
        fps = scene.render.fps
        fps_base = getattr(scene.render, "fps_base", 1.0)
        if fps_base <= 0:
            fps_base = 1.0
        return float(fps) / float(fps_base)

    def time_to_frame(self, time_seconds: float, fps: float = None) -> float:
        """
        Converts seconds to Blender timeline frame using actual scene FPS.
        
        Args:
            time_seconds: Time in seconds.
            fps: Optional FPS override. If None, queries the active scene FPS.
            
        Returns:
            Blender frame number (float).
        """
        if fps is None:
            fps = self.get_scene_fps()
        return round(float(time_seconds) * fps, 3)

    def frame_to_time(self, frame: float, fps: float = None) -> float:
        """
        Converts Blender timeline frame to seconds using actual scene FPS.
        
        Args:
            frame: Blender frame number.
            fps: Optional FPS override. If None, queries the active scene FPS.
            
        Returns:
            Time in seconds (float).
        """
        if fps is None:
            fps = self.get_scene_fps()
        if fps <= 0:
            raise ValueError(f"Invalid FPS: {fps}")
        return round(float(frame) / fps, 4)

    def load(self, json_path: str, validate_audio: bool = True):
        """
        Loads and strictly validates a LipSync JSON timeline file.
        
        Args:
            json_path: Path to the JSON file.
            validate_audio: If True and audio file exists, checks duration consistency.
        """
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"LipSync JSON file not found: {json_path}")

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                content = json.load(f)
        except Exception as e:
            raise ValueError(f"Malformed LipSync JSON in '{json_path}': {str(e)}")

        if not isinstance(content, dict):
            raise ValueError(f"Malformed LipSync JSON: root must be a JSON object, got {type(content)}")

        # Validate required top-level keys
        for req_key in ["duration_seconds", "visemes"]:
            if req_key not in content:
                raise ValueError(f"Missing required key '{req_key}' in LipSync JSON: {json_path}")

        duration = float(content["duration_seconds"])
        if duration < 0:
            raise ValueError(f"Invalid negative duration '{duration}' in LipSync JSON: {json_path}")

        visemes_list = content["visemes"]
        if not isinstance(visemes_list, list):
            raise ValueError(f"'visemes' field must be a list in {json_path}")

        # Validate segments and viseme names
        prev_end = 0.0
        validated_visemes = []
        for i, seg in enumerate(visemes_list):
            if not isinstance(seg, dict):
                raise ValueError(f"Segment #{i} is not a dictionary in {json_path}")
            if "start" not in seg or "end" not in seg or "viseme" not in seg:
                raise ValueError(f"Segment #{i} missing start/end/viseme fields: {seg}")

            start_t = float(seg["start"])
            end_t = float(seg["end"])
            vis_name = str(seg["viseme"]).strip()
            intensity = float(seg.get("intensity", 1.0))

            if start_t < 0 or end_t < 0:
                raise ValueError(f"Segment #{i} has negative timestamp: start={start_t}, end={end_t}")
            if start_t > end_t:
                raise ValueError(f"Segment #{i} has inverted timestamps: start={start_t} > end={end_t}")

            # Check viseme validity against allowed visemes
            if vis_name not in self.allowed_visemes:
                raise ValueError(f"Unknown viseme '{vis_name}' at segment #{i} in {json_path}. Allowed: {sorted(list(self.allowed_visemes))}")

            # Verify that the corresponding Shape Key exists in Blender mesh
            sk_target = self.face_controller.VISEMES.get(vis_name.lower())
            if not sk_target or sk_target not in self.face_controller.key_blocks:
                raise KeyError(f"Required Shape Key '{sk_target}' for viseme '{vis_name}' not found on mesh '{self.mesh_name}'")

            validated_visemes.append({
                "start": start_t,
                "end": end_t,
                "viseme": vis_name,
                "intensity": intensity
            })
            prev_end = end_t

        # Validate audio duration if audio file exists and requested
        audio_path = content.get("audio_file")
        if validate_audio and audio_path and os.path.exists(audio_path):
            try:
                with wave.open(audio_path, "rb") as w:
                    n_frames = w.getnframes()
                    sr = w.getframerate()
                    actual_wav_duration = round(n_frames / float(sr), 4)
                if abs(actual_wav_duration - duration) > 0.15:
                    raise LipSyncDurationMismatchError(
                        f"Audio/JSON duration mismatch in {json_path}: JSON specifies {duration}s, "
                        f"but WAV header in '{audio_path}' specifies {actual_wav_duration}s."
                    )
            except wave.Error as we:
                raise ValueError(f"Error reading referenced WAV file '{audio_path}': {str(we)}")

        # Store parsed state
        self.json_path = os.path.abspath(json_path)
        self.data = content
        self.audio_file = audio_path
        self.language = content.get("language", "en")
        self.duration_seconds = duration
        self.transition_ms = float(content.get("transition_ms", 50.0))
        self.transition_seconds = max(0.001, self.transition_ms / 1000.0)
        self.visemes = validated_visemes

    def evaluate_at_time(self, time_seconds: float, custom_transition_ms: float = None):
        """
        Determines the viseme blending state at a specific timestamp.
        
        Performs smooth interpolation (crossfading) between adjacent visemes
        during boundary transitions, preventing abrupt hard-snapping.
        
        Args:
            time_seconds: Current playback time in seconds.
            custom_transition_ms: Optional override for transition smoothing window.
            
        Returns:
            dict containing:
                "type": "single" or "transition" or "silence",
                "viseme_a": primary or outgoing viseme name,
                "viseme_b": incoming viseme name (if in transition),
                "factor": blend factor 0.0 to 1.0,
                "intensity": target intensity
        """
        if not self.visemes:
            return {"type": "silence", "viseme_a": "Silence", "viseme_b": None, "factor": 0.0, "intensity": 0.0}

        t = float(time_seconds)
        trans_sec = (custom_transition_ms / 1000.0) if custom_transition_ms is not None else self.transition_seconds

        # Out of bounds: before start or past audio duration
        if t < 0.0 or t >= self.duration_seconds:
            return {"type": "silence", "viseme_a": "Silence", "viseme_b": None, "factor": 0.0, "intensity": 0.0}

        # Find active segment
        num_segs = len(self.visemes)
        active_idx = -1
        for i, seg in enumerate(self.visemes):
            if seg["start"] <= t < seg["end"]:
                active_idx = i
                break

        if active_idx == -1:
            # Fallback if floating-point edge at exact end
            if abs(t - self.duration_seconds) < 0.001:
                active_idx = num_segs - 1
            else:
                return {"type": "silence", "viseme_a": "Silence", "viseme_b": None, "factor": 0.0, "intensity": 0.0}

        seg = self.visemes[active_idx]
        vis_cur = seg["viseme"]
        intensity_cur = seg["intensity"]

        # Check for smooth transition into next segment
        # Transition window spans centered around segment boundary: [boundary - trans/2, boundary + trans/2]
        half_trans = trans_sec / 2.0

        # Boundary with next segment
        if active_idx + 1 < num_segs:
            next_seg = self.visemes[active_idx + 1]
            vis_next = next_seg["viseme"]
            boundary = seg["end"]

            # If within transition window towards next segment
            if (boundary - half_trans) <= t < boundary:
                # First half of crossfade (outgoing vis_cur -> vis_next)
                trans_start = boundary - half_trans
                trans_end = boundary + half_trans
                factor = (t - trans_start) / (trans_end - trans_start)
                factor = max(0.0, min(1.0, factor))
                return {
                    "type": "transition",
                    "viseme_a": vis_cur,
                    "viseme_b": vis_next,
                    "factor": factor,
                    "intensity": intensity_cur
                }

        # Boundary with previous segment
        if active_idx > 0:
            prev_seg = self.visemes[active_idx - 1]
            vis_prev = prev_seg["viseme"]
            prev_boundary = seg["start"]

            # If within transition window from previous segment
            if prev_boundary <= t < (prev_boundary + half_trans):
                # Second half of crossfade (incoming vis_prev -> vis_cur)
                trans_start = prev_boundary - half_trans
                trans_end = prev_boundary + half_trans
                factor = (t - trans_start) / (trans_end - trans_start)
                factor = max(0.0, min(1.0, factor))
                return {
                    "type": "transition",
                    "viseme_a": vis_prev,
                    "viseme_b": vis_cur,
                    "factor": factor,
                    "intensity": intensity_cur
                }

        # Pure segment body (no boundary crossfade)
        return {
            "type": "single",
            "viseme_a": vis_cur,
            "viseme_b": None,
            "factor": 1.0,
            "intensity": intensity_cur
        }

    def update(self, time_seconds: float, custom_transition_ms: float = None):
        """
        Updates the Chacha Shape Keys to match the lip-sync state at time_seconds.
        DOES NOT alter active emotions, blinks, modular shapes, or body Actions.
        
        Args:
            time_seconds: Current playback time in seconds.
            custom_transition_ms: Optional override for smoothing crossfade window.
        """
        eval_res = self.evaluate_at_time(time_seconds, custom_transition_ms=custom_transition_ms)

        if eval_res["type"] == "silence":
            # Set to Viseme_Silence or clear all speech visemes
            self.face_controller.set_viseme("Silence", 1.0)
        elif eval_res["type"] == "transition":
            self.face_controller.transition_viseme(
                from_viseme=eval_res["viseme_a"],
                to_viseme=eval_res["viseme_b"],
                factor=eval_res["factor"],
                intensity=eval_res["intensity"]
            )
            dom_vis = eval_res["viseme_b"] if eval_res["factor"] >= 0.5 else eval_res["viseme_a"]
            self.face_controller.current_viseme = dom_vis.lower()
            self.face_controller.current_viseme_intensity = eval_res["intensity"]
        else:
            self.face_controller.set_viseme(
                viseme_name=eval_res["viseme_a"],
                intensity=eval_res["intensity"]
            )

    def get_active_visemes(self) -> dict:
        """Returns dictionary of currently active speech viseme shape keys and their weights."""
        active = {}
        for name, sk_name in self.face_controller.VISEMES.items():
            if sk_name in self.face_controller.key_blocks:
                val = self.face_controller.key_blocks[sk_name].value
                if val > 0.001:
                    active[sk_name] = round(val, 4)
        return active

    def update_frame(self, frame: float, start_frame: int = 1, fps: float = None):
        """
        Updates the lip-sync state based on a Blender timeline frame.
        
        Args:
            frame: Current frame number.
            start_frame: Starting frame offset (default: 1).
            fps: Optional scene FPS override.
        """
        if fps is None:
            fps = self.get_scene_fps()
        rel_frame = frame - start_frame
        time_seconds = rel_frame / fps
        self.update(time_seconds)

    def reset(self):
        """
        Resets only the lip-sync speech visemes to neutral (0.0).
        CRITICAL: Does NOT reset an independently active emotion or body Action.
        For example: Happy (0.8) + LipSync -> after reset: Happy (0.8) + neutral mouth.
        """
        self.face_controller.clear_viseme()

    def play(self, start_frame: int = 1):
        """
        Enables interactive timeline scrubbing / playback in Blender.
        Registers a frame_change handler that calls update_frame whenever
        the Blender timeline changes.
        """
        self.start_frame = start_frame
        self.is_playing = True
        self.attach_timeline_scrub(start_frame=start_frame)

    def stop(self):
        """Stops interactive playback and removes timeline handler."""
        self.is_playing = False
        self.detach_timeline_scrub()

    def attach_timeline_scrub(self, start_frame: int = 1):
        """
        Attaches a post frame-change handler to bpy.app.handlers.frame_change_post
        allowing timeline scrubbing to interactively preview mouth articulation.
        """
        self.detach_timeline_scrub()  # ensure clean detachment first
        self.start_frame = start_frame

        def _on_frame_change(scene):
            if not self.visemes:
                return
            current_frame = scene.frame_current
            self.update_frame(current_frame, start_frame=self.start_frame)

        self._frame_handler = _on_frame_change
        bpy.app.handlers.frame_change_post.append(self._frame_handler)

    def detach_timeline_scrub(self):
        """Removes the timeline frame-change handler."""
        if self._frame_handler and self._frame_handler in bpy.app.handlers.frame_change_post:
            bpy.app.handlers.frame_change_post.remove(self._frame_handler)
        self._frame_handler = None

    def bake_lipsync_to_shape_keys(self, action_name: str = None, start_frame: int = 1, step: int = 1) -> bpy.types.Action:
        """
        OPTIONAL non-destructive utility to bake lip-sync into a NEW dedicated facial Action.
        
        Rules:
        - Creates a NEW dedicated Action attached to mesh.data.shape_keys.animation_data
        - NEVER modifies or overwrites body Actions (Chacha_Idle, Chacha_Nod, etc.)
        - NEVER modifies underlying mesh topology or vertices
        - Is 100% reversible via clear_baked_lipsync()
        - Is NOT required for normal runtime playback
        
        Args:
            action_name: Name for the facial action. Defaults to 'Action_LipSync_<json_basename>'.
            start_frame: Start frame on the timeline.
            step: Frame step for keyframing (default: 1 for every frame).
            
        Returns:
            The created bpy.types.Action object.
        """
        if not self.visemes:
            raise ValueError("No lip-sync data loaded to bake.")

        mesh_obj = self.face_controller.mesh_obj
        if not mesh_obj.data.shape_keys:
            raise RuntimeError("Target mesh has no Shape Keys.")

        sk_data = mesh_obj.data.shape_keys
        if not sk_data.animation_data:
            sk_data.animation_data_create()

        fps = self.get_scene_fps()
        total_frames = int(math.ceil(self.duration_seconds * fps))
        end_frame = start_frame + total_frames

        base_name = os.path.splitext(os.path.basename(self.json_path or "lipsync"))[0]
        act_name = action_name or f"Action_LipSync_{base_name}"

        # Create NEW dedicated Action for Shape Keys
        facial_action = bpy.data.actions.new(name=act_name)
        sk_data.animation_data.action = facial_action

        # Viseme Shape Key block names to key
        viseme_sk_names = [self.face_controller.VISEMES[k] for k in self.face_controller.VISEMES]

        # Keyframe across duration
        for f in range(start_frame, end_frame + 1, step):
            rel_t = (f - start_frame) / fps
            self.update(rel_t)

            for sk_name in viseme_sk_names:
                sk_block = self.face_controller.key_blocks.get(sk_name)
                if sk_block:
                    sk_block.keyframe_insert(data_path="value", frame=f)

        return facial_action

    def clear_baked_lipsync(self):
        """
        Safely clears any baked facial lip-sync Action from the Shape Keys block
        and resets speech visemes to neutral rest pose.
        """
        mesh_obj = self.face_controller.mesh_obj
        if mesh_obj and mesh_obj.data.shape_keys and mesh_obj.data.shape_keys.animation_data:
            mesh_obj.data.shape_keys.animation_data.action = None
        self.reset()


# Helper convenience functions
def load_and_play(json_path: str, start_frame: int = 1) -> ChachaLipSyncPlayer:
    """Convenience function to load a LipSync JSON and attach timeline preview."""
    player = ChachaLipSyncPlayer()
    player.load(json_path)
    player.play(start_frame=start_frame)
    return player
