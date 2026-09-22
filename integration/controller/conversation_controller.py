"""Conversation state machine and pipeline orchestrator."""

from __future__ import annotations

import logging
import threading
import time
from typing import Callable, Any

from integration.api.brain_client import BrainClient
from integration.config.integration_config import IntegrationConfig, load_integration_config
from integration.models.brain_response import (
    AvatarPresentation,
    BrainResponse,
    ConversationState,
    EmotionType,
    GestureType,
)

logger = logging.getLogger("integration.conversation_controller")


class ConversationController:
    """Manages full lifecycle of mascot interaction: IDLE -> LISTENING -> PROCESSING -> THINKING -> SPEAKING -> IDLE."""

    def __init__(
        self,
        brain_client: BrainClient | None = None,
        config: IntegrationConfig | None = None,
        on_state_change: Callable[[AvatarPresentation], None] | None = None,
    ) -> None:
        self.config = config or load_integration_config()
        self.brain_client = brain_client or BrainClient(self.config)
        self.on_state_change = on_state_change
        self._lock = threading.Lock()
        self._current_state = ConversationState.IDLE
        self._last_presentation = AvatarPresentation(state=ConversationState.IDLE)

    @property
    def current_state(self) -> ConversationState:
        with self._lock:
            return self._current_state

    @property
    def is_busy(self) -> bool:
        with self._lock:
            return self._current_state != ConversationState.IDLE

    def _set_state(self, presentation: AvatarPresentation) -> None:
        with self._lock:
            self._current_state = presentation.state
            self._last_presentation = presentation
        logger.info(f"[Integration State] -> {presentation.state.value} (Emotion: {presentation.emotion.value}, Gesture: {presentation.gesture.value})")
        if self.on_state_change:
            try:
                self.on_state_change(presentation)
            except Exception as e:
                logger.error(f"[Integration] Error in state change listener: {e}")

    def process_text_question(self, question: str, language: str = "hi") -> AvatarPresentation:
        """Process a text question through the state machine synchronously / thread-safely."""
        if self.is_busy:
            logger.warning("[Integration] Conversation controller is busy. Ignoring duplicate request.")
            return self._last_presentation

        if not question or not question.strip():
            logger.warning("[Integration] Empty question supplied to conversation controller.")
            pres = AvatarPresentation(
                state=ConversationState.IDLE,
                question="",
                answer="Please enter a question to ask Chacha Mascot.",
                mode="insufficient-evidence",
                language=language,
                emotion=EmotionType.NEUTRAL,
                gesture=GestureType.IDLE,
            )
            self._set_state(pres)
            return pres

        # State 1: PROCESSING
        self._set_state(AvatarPresentation(
            state=ConversationState.PROCESSING,
            question=question,
            language=language,
            emotion=EmotionType.NEUTRAL,
            gesture=GestureType.IDLE,
        ))

        # State 2: THINKING
        self._set_state(AvatarPresentation(
            state=ConversationState.THINKING,
            question=question,
            language=language,
            emotion=EmotionType.THINKING,
            gesture=GestureType.THINKING,
        ))

        # Step 3: Query Brain API
        try:
            brain_resp = self.brain_client.ask(question, language=language)
        except Exception as e:
            logger.error(f"[Integration] Brain query failed: {e}")
            error_pres = AvatarPresentation(
                state=ConversationState.ERROR,
                question=question,
                answer="Sorry, I'm having trouble connecting right now.",
                mode="insufficient-evidence",
                language=language,
                emotion=EmotionType.NEUTRAL,
                gesture=GestureType.IDLE,
                error_message=str(e),
            )
            self._set_state(error_pres)
            time.sleep(0.5)
            self._set_state(AvatarPresentation(state=ConversationState.IDLE, language=language))
            return error_pres

        # State 4: SPEAKING
        speaking_pres = AvatarPresentation(
            state=ConversationState.SPEAKING,
            question=question,
            answer=brain_resp.answer,
            mode=brain_resp.mode,
            citations=brain_resp.citations,
            language=brain_resp.language,
            emotion=brain_resp.emotion,
            gesture=brain_resp.gesture,
        )
        self._set_state(speaking_pres)

        return speaking_pres

    def finish_speaking(self, language: str = "hi") -> AvatarPresentation:
        """Explicit trigger to transition from SPEAKING back to IDLE after audio finishes."""
        idle_pres = AvatarPresentation(
            state=ConversationState.IDLE,
            question=self._last_presentation.question,
            answer=self._last_presentation.answer,
            mode=self._last_presentation.mode,
            citations=self._last_presentation.citations,
            language=language,
            emotion=EmotionType.NEUTRAL,
            gesture=GestureType.IDLE,
        )
        self._set_state(idle_pres)
        return idle_pres

    def start_listening(self, language: str = "hi") -> AvatarPresentation:
        """Trigger LISTENING state for voice recording."""
        if self.is_busy and self.current_state != ConversationState.IDLE:
            logger.warning("[Integration] Cannot start listening while state is active.")
            return self._last_presentation

        listening_pres = AvatarPresentation(
            state=ConversationState.LISTENING,
            language=language,
            emotion=EmotionType.NEUTRAL,
            gesture=GestureType.WAVE,
        )
        self._set_state(listening_pres)
        return listening_pres

    def cancel_to_idle(self, error_message: str | None = None) -> AvatarPresentation:
        """Emergency reset path to prevent permanent hanging."""
        target_state = ConversationState.ERROR if error_message else ConversationState.IDLE
        reset_pres = AvatarPresentation(
            state=target_state,
            answer=error_message or "",
            emotion=EmotionType.NEUTRAL,
            gesture=GestureType.IDLE,
            error_message=error_message,
        )
        self._set_state(reset_pres)
        if target_state == ConversationState.ERROR:
            time.sleep(0.2)
            final_idle = AvatarPresentation(state=ConversationState.IDLE)
            self._set_state(final_idle)
            return final_idle
        return reset_pres
