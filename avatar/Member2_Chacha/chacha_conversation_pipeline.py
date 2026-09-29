"""
Chacha Chaudhary - End-to-End Conversation Pipeline Coordinator
Stage 12B: Complete Conversation Flow Integration

Coordinates the full multimodal loop:
    USER
     ↓
    MICROPHONE (ChachaMicrophone)
     ↓
    SPEECH-TO-TEXT (ChachaSTTPipeline / Vosk Offline)
     ↓
    NORMALIZED TEXT
     ↓
    AI REASONING (Member1AIProvider / MockAIProvider)
     ↓
    RESPONSE TEXT + EMOTION + GESTURE
     ↓
    TEXT-TO-SPEECH (ChachaTTSPipeline)
     ↓
    16-BIT MONO 16KHZ WAV
     ↓
    ACOUSTIC LIP-SYNC (ChachaLipSyncPipeline / Rhubarb)
     ↓
    VISEME TIMELINE JSON
     ↓
    AVATAR PLAYBACK (ChachaAvatarController / ChachaLipSyncPlayer)
     ↓
    ANIMATED AVATAR (Body + Emotion + Visemes + Procedural Blinks)
"""

import os
import sys
import json
import time
from typing import Optional, Dict, Any

# Ensure output root directory is in sys.path
_current_dir = os.path.dirname(os.path.abspath(__file__))
_output_dir = os.path.dirname(_current_dir)
if _output_dir not in sys.path:
    sys.path.insert(0, _output_dir)
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

# Import existing core modules
from chacha_microphone import ChachaMicrophone, MicrophoneError
from chacha_stt_pipeline import ChachaSTTPipeline, STTError, normalize_text
from chacha_tts_pipeline import ChachaTTSPipeline, BaseTTSProvider, EdgeTTSProvider
from chacha_lipsync_pipeline import ChachaLipSyncPipeline
from ai_provider import BaseAIProvider, MockAIProvider, Member1AIProvider, AIProviderError, EmptyAIResponseError

# Blender avatar controller is imported conditionally when running in Blender environment
try:
    from chacha_avatar_controller import ChachaAvatarController, AvatarState
    AVATAR_CONTROLLER_AVAILABLE = True
except Exception:
    AVATAR_CONTROLLER_AVAILABLE = False


class PipelineError(Exception):
    """Base exception for conversation pipeline failures."""
    pass


class ChachaConversationPipeline:
    """
    High-level orchestrator connecting microphone, STT, AI adapter, TTS, Rhubarb,
    and avatar behavioral state machine.
    """

    def __init__(self, ai_provider: Optional[BaseAIProvider] = None, config_path: Optional[str] = None):
        # 1. Load centralized configuration
        cfg_file = config_path or os.path.join(_current_dir, "integration_config.json")
        if os.path.exists(cfg_file):
            with open(cfg_file, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        else:
            self.config = {}

        # 2. Initialize modular subsystems
        self.microphone = ChachaMicrophone()
        self.stt = ChachaSTTPipeline(provider_type="local")
        self.ai = ai_provider or MockAIProvider()
        self.tts = ChachaTTSPipeline()
        self.lipsync = ChachaLipSyncPipeline()

        # Paths
        paths = self.config.get("paths", {})
        self.audio_input_dir = os.path.join(_output_dir, "Audio", "Input")
        self.audio_gen_dir = os.path.join(_output_dir, "Audio", "Generated")
        self.lipsync_dir = os.path.join(_output_dir, "LipSync")
        self.log_dir = os.path.join(_current_dir, "Logs")

        for d in [self.audio_input_dir, self.audio_gen_dir, self.lipsync_dir, self.log_dir]:
            os.makedirs(d, exist_ok=True)

    def process_conversation_turn(
        self,
        input_text: Optional[str] = None,
        input_audio_path: Optional[str] = None,
        language: str = "en",
        avatar_controller: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Executes a single end-to-end conversation turn.
        
        Args:
            input_text: Direct text input (bypasses microphone/STT for deterministic testing).
            input_audio_path: Path to user speech WAV (transcribed via Vosk STT).
            language: 'en' or 'hi'.
            avatar_controller: Optional active ChachaAvatarController instance.
            
        Returns:
            Structured dictionary recording all intermediate and final pipeline states.
        """
        lang = str(language).lower().strip()
        if lang not in ["en", "hi"]:
            raise PipelineError(f"Unsupported language '{language}'. Supported: 'en', 'hi'")

        state_history = []
        if avatar_controller:
            avatar_controller.set_state("idle")
            state_history.append("idle")

        raw_transcript = None
        normalized_query = None

        # -------------------------------------------------------------
        # Step 1: Input Acquisition (Audio -> STT or Direct Text)
        # -------------------------------------------------------------
        if input_audio_path:
            if not os.path.exists(input_audio_path):
                raise FileNotFoundError(f"Input audio file not found: {input_audio_path}")

            if avatar_controller:
                avatar_controller.set_state("listening")
                state_history.append("listening")

            try:
                stt_res = self.stt.transcribe(input_audio_path, language=lang)
            except Exception as e:
                raise PipelineError(f"STT transcription failed: {str(e)}")

            raw_transcript = stt_res.get("raw_text", "")
            normalized_query = stt_res.get("text", "")

            if not normalized_query or not normalized_query.strip():
                raise PipelineError(f"STT produced empty transcription from '{input_audio_path}'")

        elif input_text:
            raw_transcript = input_text
            normalized_query = normalize_text(input_text)
            if not normalized_query:
                raise PipelineError("Input text query is empty.")
        else:
            raise PipelineError("Neither input_text nor input_audio_path provided.")

        # -------------------------------------------------------------
        # Step 2: AI Reasoning (Member 1 / Mock)
        # -------------------------------------------------------------
        if avatar_controller:
            avatar_controller.set_state("thinking")
            state_history.append("thinking")

        try:
            ai_res = self.ai.respond(text=normalized_query, language=lang)
        except Exception as e:
            raise PipelineError(f"AI response generation failed: {str(e)}")

        response_text = ai_res.get("response_text", "")
        if not response_text or not response_text.strip():
            raise PipelineError("AI provider returned empty response text.")

        emotion = ai_res.get("emotion")
        emotion_intensity = float(ai_res.get("emotion_intensity", 0.0))
        body_action = ai_res.get("body_action")

        # -------------------------------------------------------------
        # Step 3: Text-to-Speech (Response Text -> WAV)
        # -------------------------------------------------------------
        # Generate clean filename slug
        ts = int(time.time())
        slug = f"conv_{lang}_{ts}"
        output_wav = os.path.join(self.audio_gen_dir, f"{slug}.wav")

        try:
            tts_res = self.tts.provider.synthesize_to_wav(
                text=response_text,
                language=lang,
                voice=None,
                output_wav=output_wav
            )
        except Exception as e:
            raise PipelineError(f"TTS synthesis failed: {str(e)}")

        if not os.path.exists(output_wav) or os.path.getsize(output_wav) < 44:
            raise PipelineError(f"TTS output WAV missing or corrupt: {output_wav}")

        audio_duration = float(tts_res.get("duration_seconds", 0.0))

        # -------------------------------------------------------------
        # Step 4: Rhubarb Lip-Sync Analysis (WAV -> Viseme JSON)
        # -------------------------------------------------------------
        output_json = os.path.join(self.lipsync_dir, f"{slug}.json")
        try:
            analysis_dict = self.lipsync.analyze_audio(
                audio_path=output_wav,
                language=lang,
                transition_ms=float(self.config.get("rhubarb", {}).get("transition_ms", 50.0))
            )
            self.lipsync.save_lipsync_json(analysis_dict, output_json)
        except Exception as e:
            raise PipelineError(f"Rhubarb lip-sync analysis failed: {str(e)}")

        if not os.path.exists(output_json):
            raise PipelineError(f"LipSync JSON file was not created: {output_json}")

        # -------------------------------------------------------------
        # Step 5: Avatar Playback Execution
        # -------------------------------------------------------------
        final_state = "idle"
        if avatar_controller:
            # Set emotion if provided
            if emotion:
                avatar_controller.set_emotion(emotion, emotion_intensity)

            # Set body gesture if provided
            if body_action:
                avatar_controller.play_body_action(body_action)

            # Start lip-sync: automatically transitions to SPEAKING
            avatar_controller.start_lipsync(output_json)
            state_history.append("speaking")

            # Simulate playback cycle: sample speech midpoint and end
            mid_t = audio_duration / 2.0
            avatar_controller.update(mid_t)

            # Complete speech: resets lip-sync, preserves emotion, returns to IDLE
            avatar_controller.update(audio_duration + 0.1)
            final_state = avatar_controller.state
            state_history.append(final_state)

        # -------------------------------------------------------------
        # Step 6: Structured Logging Record
        # -------------------------------------------------------------
        log_record = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "input_language": lang,
            "input_type": "audio" if input_audio_path else "text",
            "input_text": raw_transcript,
            "normalized_text": normalized_query,
            "ai_provider": self.ai.__class__.__name__,
            "is_mock_ai": getattr(self.ai, "DEVELOPMENT_DISCLAIMER", None) is not None,
            "response_text": response_text,
            "tts_audio": os.path.abspath(output_wav),
            "audio_duration_seconds": audio_duration,
            "lipsync_json": os.path.abspath(output_json),
            "emotion": emotion,
            "emotion_intensity": emotion_intensity,
            "body_action": body_action,
            "state_sequence": state_history,
            "final_state": final_state
        }

        # Write log file
        log_file = os.path.join(self.log_dir, f"log_{slug}.json")
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(log_record, f, indent=2, ensure_ascii=False)

        return log_record

    def test_conversation(self, text: str, language: str = "en", avatar_controller: Optional[Any] = None) -> Dict[str, Any]:
        """Convenience method for TEXT-ONLY end-to-end conversation test."""
        return self.process_conversation_turn(
            input_text=text,
            language=language,
            avatar_controller=avatar_controller
        )

    def run_voice_conversation(
        self,
        audio_file: Optional[str] = None,
        duration_seconds: float = 3.0,
        language: str = "en",
        avatar_controller: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Convenience method for MICROPHONE / AUDIO end-to-end conversation test.
        If audio_file is not supplied, records live from default microphone.
        """
        if not audio_file:
            # Capture live audio from host microphone
            target_wav = os.path.join(self.audio_input_dir, f"mic_turn_{language}_{int(time.time())}.wav")
            audio_file = self.microphone.record_once(duration_seconds=duration_seconds, output_path=target_wav)

        return self.process_conversation_turn(
            input_audio_path=audio_file,
            language=language,
            avatar_controller=avatar_controller
        )
