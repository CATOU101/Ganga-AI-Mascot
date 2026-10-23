"""Conversation state machine and pipeline orchestrator."""

from __future__ import annotations

import logging
import threading
import time
from typing import Callable, Any

from integration.api.brain_client import BrainClient
from integration.avatar.response_text import spoken_response
from integration.config.integration_config import IntegrationConfig, load_integration_config
from integration.models.brain_response import (
    AvatarPresentation,
    BrainResponse,
    CitationItem,
    ConversationState,
    EmotionType,
    GestureType,
)
from integration.water_quality import (
    CPCBWaterQualityError,
    CPCBWaterQualityService,
    format_water_quality_answer,
    is_water_quality_query,
    parse_water_quality_request,
)

logger = logging.getLogger("integration.conversation_controller")


class ConversationController:
    """Manages full lifecycle of mascot interaction: IDLE -> LISTENING -> PROCESSING -> THINKING -> SPEAKING -> IDLE."""

    def __init__(
        self,
        brain_client: BrainClient | None = None,
        config: IntegrationConfig | None = None,
        on_state_change: Callable[[AvatarPresentation], None] | None = None,
        water_quality_service: CPCBWaterQualityService | None = None,
    ) -> None:
        self.config = config or load_integration_config()
        self.brain_client = brain_client or BrainClient(self.config)
        self.water_quality_service = water_quality_service
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
                logger.error("[Integration] State change listener failed (%s).", type(e).__name__)

    def process_text_question(
        self,
        question: str,
        input_language: str = "hi",
        output_language: str = "hi",
        top_k: int | None = None,
        language: str | None = None,
        translation_consent: bool = True,
    ) -> AvatarPresentation:
        """Process a text question through the state machine synchronously / thread-safely."""
        in_lang = (input_language or language or "hi").lower().strip()
        out_lang = (output_language or language or "hi").lower().strip()

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
                input_language=in_lang,
                output_language=out_lang,
                language=out_lang,
                emotion=EmotionType.NEUTRAL,
                gesture=GestureType.IDLE,
            )
            self._set_state(pres)
            return pres

        # State 1: PROCESSING
        self._set_state(AvatarPresentation(
            state=ConversationState.PROCESSING,
            question=question,
            input_language=in_lang,
            output_language=out_lang,
            language=out_lang,
            emotion=EmotionType.NEUTRAL,
            gesture=GestureType.IDLE,
        ))

        # State 2: THINKING
        self._set_state(AvatarPresentation(
            state=ConversationState.THINKING,
            question=question,
            input_language=in_lang,
            output_language=out_lang,
            language=out_lang,
            emotion=EmotionType.THINKING,
            gesture=GestureType.THINKING,
        ))

        # Live CPCB readings are handled before Brain's current-information fallback.
        if self.water_quality_service and is_water_quality_query(question):
            water_request = parse_water_quality_request(question)
            try:
                readings = self.water_quality_service.readings(water_request)
                answer = format_water_quality_answer(water_request, readings)
                mode = "live-water-quality"
            except CPCBWaterQualityError as error:
                logger.error("[Integration] CPCB water-quality query failed (%s).", type(error).__name__)
                answer = (
                    "I couldn't retrieve the requested live water-quality data from CPCB just now. "
                    "Please try again later; I won't substitute older or unrelated readings."
                )
                mode = "live-water-quality-unavailable"

            if out_lang != "en":
                from brain.translator import TranslationError, translate_text

                english_answer = answer
                try:
                    answer = translate_text(answer, "en", out_lang, allow_external=translation_consent)
                except TranslationError:
                    logger.warning("[Integration] CPCB answer translation unavailable or disabled.")
                    answer = (
                        f"{english_answer}\n\n"
                        f"The readings remain in English because translation to {out_lang} was disabled or unavailable."
                    )
                    mode = "live-water-quality-translation-unavailable"

            speaking_pres = AvatarPresentation(
                state=ConversationState.SPEAKING,
                question=question,
                answer=answer,
                spoken_text=spoken_response(answer),
                mode=mode,
                citations=[
                    CitationItem(source="CPCB Real-Time Water Quality Monitoring System")
                ],
                input_language=in_lang,
                output_language=out_lang,
                language=out_lang,
                emotion=EmotionType.NEUTRAL,
                gesture=GestureType.EXPLAINING,
            )
            self._set_state(speaking_pres)
            return speaking_pres

        # Step 3: Query Brain API
        try:
            brain_resp = self.brain_client.ask(
                question, input_language=in_lang, output_language=out_lang,
                top_k=top_k, translation_consent=translation_consent,
            )
        except Exception as e:
            from brain.translator import TranslationConsentRequired

            if isinstance(e, TranslationConsentRequired):
                self._set_state(AvatarPresentation(
                    state=ConversationState.IDLE,
                    input_language=in_lang,
                    output_language=out_lang,
                    language=out_lang,
                ))
                raise
            logger.error("[Integration] Brain query failed (%s).", type(e).__name__)
            error_pres = AvatarPresentation(
                state=ConversationState.ERROR,
                question=question,
                answer="Sorry, I'm having trouble connecting right now.",
                mode="insufficient-evidence",
                input_language=in_lang,
                output_language=out_lang,
                language=out_lang,
                emotion=EmotionType.NEUTRAL,
                gesture=GestureType.IDLE,
                error_message="The Brain could not process this request.",
            )
            self._set_state(error_pres)
            time.sleep(0.5)
            self._set_state(AvatarPresentation(state=ConversationState.IDLE, input_language=in_lang, output_language=out_lang, language=out_lang))
            return error_pres

        # State 4: SPEAKING
        speaking_pres = AvatarPresentation(
            state=ConversationState.SPEAKING,
            question=question,
            answer=brain_resp.answer,
            spoken_text=spoken_response(brain_resp.answer),
            mode=brain_resp.mode,
            citations=brain_resp.citations,
            input_language=brain_resp.input_language,
            output_language=brain_resp.output_language,
            language=brain_resp.output_language,
            emotion=brain_resp.emotion,
            gesture=brain_resp.gesture,
        )
        self._set_state(speaking_pres)

        return speaking_pres

    def finish_speaking(self, input_language: str = "hi", output_language: str = "hi", language: str | None = None) -> AvatarPresentation:
        """Explicit trigger to transition from SPEAKING back to IDLE after audio finishes."""
        in_lang = (input_language or language or "hi").lower().strip()
        out_lang = (output_language or language or "hi").lower().strip()
        idle_pres = AvatarPresentation(
            state=ConversationState.IDLE,
            question=self._last_presentation.question,
            answer=self._last_presentation.answer,
            mode=self._last_presentation.mode,
            citations=self._last_presentation.citations,
            input_language=in_lang,
            output_language=out_lang,
            language=out_lang,
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
