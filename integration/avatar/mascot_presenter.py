"""Presenter component coordinating avatar state, animation mappers, and lip-sync payload."""

from __future__ import annotations

import logging
from integration.avatar.emotion_mapper import map_emotion
from integration.avatar.gesture_mapper import map_gesture
from integration.avatar.lipsync import LipSyncAnalyzer
from integration.models.brain_response import AvatarPresentation, BrainResponse, ConversationState
from integration.voice.tts_adapter import TTSAudioResult

logger = logging.getLogger("integration.mascot_presenter")


class MascotPresenter:
    def __init__(self) -> None:
        self.lipsync_analyzer = LipSyncAnalyzer()

    def create_presentation(
        self,
        brain_response: BrainResponse,
        conversation_state: ConversationState = ConversationState.SPEAKING,
        tts_result: TTSAudioResult | None = None,
    ) -> AvatarPresentation:
        """Build AvatarPresentation object with verified emotion, gesture, and lip-sync values."""
        emotion = map_emotion(brain_response.emotion, brain_response.mode)
        gesture = map_gesture(brain_response.gesture, brain_response.mode)
        
        rms_lip_sync: list[float] = []
        audio_b64: str | None = None

        if tts_result:
            audio_b64 = tts_result.audio_base64
            rms_lip_sync = self.lipsync_analyzer.compute_rms_frames(tts_result.pcm_samples)

        return AvatarPresentation(
            state=conversation_state,
            answer=brain_response.answer,
            mode=brain_response.mode,
            citations=brain_response.citations,
            language=brain_response.language,
            emotion=emotion,
            gesture=gesture,
            audio_data_base64=audio_b64,
            rms_lip_sync=rms_lip_sync,
        )
