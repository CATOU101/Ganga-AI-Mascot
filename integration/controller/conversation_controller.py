"""Conversation state machine and pipeline orchestrator."""

from __future__ import annotations

import logging
import re
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
    build_water_data_tables,
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
        from integration.external_sources import ExternalSourceService
        from integration.response_cache import TTLCache

        self.external_source_service = ExternalSourceService()
        self._general_response_cache = TTLCache[dict](ttl_seconds=900)
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

        # CPCB intent and station names are matched against the English rule set.
        # Normalize non-English text before classification, preserving the original
        # question in the presentation and letting translation failures surface.
        cpcb_query = question
        english_cues = {
            "what", "who", "where", "when", "why", "how", "is", "are", "was", "were",
            "does", "do", "did", "can", "could", "tell", "explain", "about", "the", "of",
            "current", "water", "quality", "level", "purpose", "created",
        }
        ascii_words = set(question.casefold().split())
        contains_non_ascii = any(not char.isascii() for char in question)
        likely_english = bool(ascii_words & english_cues)
        if in_lang != "en" and (contains_non_ascii or not likely_english):
            from brain.translator import translate_text

            cpcb_query = translate_text(
                question, in_lang, "en", allow_external=translation_consent
            )

        # Resolve simple identity and scope routes before either CPCB or RAG.
        from brain.translator import translate_text
        from integration.scope import classify_request, identity_response, scope_response

        route = classify_request(cpcb_query)
        if route and route != "general":
            if route == "other-river-context":
                from integration.supplementary_info import append_supplementary_summaries

                summaries = self.external_source_service.search_summaries(
                    cpcb_query, language=out_lang, max_sources=1
                )
                if summaries:
                    answer, external_citations = append_supplementary_summaries(
                        translate_text(
                            "The project knowledge base focuses on the Ganga. The following is brief background context from an external, community-edited source:",
                            "en", out_lang, allow_external=translation_consent,
                        ),
                        summaries,
                    )
                    citations = [CitationItem(**item) for item in external_citations]
                else:
                    answer = scope_response("unsupported-water-topic", cpcb_query)
                    citations = []
                pres = AvatarPresentation(
                    state=ConversationState.SPEAKING, question=question, answer=answer,
                    spoken_text=spoken_response(answer), mode="external-river-context" if citations else "unsupported-water-topic",
                    citations=citations, input_language=in_lang, output_language=out_lang, language=out_lang,
                    emotion=EmotionType.NEUTRAL, gesture=GestureType.EXPLAINING,
                )
                self._set_state(pres)
                return pres
            english_answer = identity_response(cpcb_query) if route == "identity" else scope_response(route, cpcb_query)
            answer = translate_text(english_answer, "en", out_lang, allow_external=translation_consent)
            pres = AvatarPresentation(
                state=ConversationState.SPEAKING,
                question=question,
                answer=answer,
                spoken_text=spoken_response(answer),
                mode=route,
                input_language=in_lang,
                output_language=out_lang,
                language=out_lang,
                emotion=EmotionType.NEUTRAL,
                gesture=GestureType.EXPLAINING,
            )
            self._set_state(pres)
            return pres

        # Live CPCB readings are handled before Brain's current-information fallback.
        if self.water_quality_service and is_water_quality_query(cpcb_query):
            water_request = parse_water_quality_request(cpcb_query)
            readings = []
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
                tables=build_water_data_tables(water_request, readings, out_lang) if mode == "live-water-quality" else [],
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

        if route == "general":
            from brain.config import load_config
            from brain.generator import GENERAL_GENERATION_FAILURE, build_generator

            from brain.answer_format import detect_answer_format
            from integration.response_cache import general_response_cache_key

            cache_key = general_response_cache_key(
                cpcb_query, out_lang, detect_answer_format(cpcb_query).cache_key
            )
            general_result = self._general_response_cache.get(cache_key) if cache_key else None
            cache_hit = general_result is not None
            if not cache_hit:
                try:
                    brain_config = load_config()
                    provider_order = getattr(brain_config, "llm_provider_order", None)
                    generator = (
                        build_generator(brain_config.llm_provider, brain_config.llm_model)
                        if provider_order is None
                        else build_generator(brain_config.llm_provider, brain_config.llm_model, provider_order)
                    )
                    general_result = generator.generate_general(cpcb_query)
                except Exception as error:
                    logger.warning("[Integration] General response generation failed (%s).", type(error).__name__)
                    general_result = {
                        "answer": GENERAL_GENERATION_FAILURE,
                        "citations": [],
                        "mode": "general-unavailable",
                    }

            generated_answer = general_result.get("answer") if isinstance(general_result, dict) else None
            if (
                isinstance(general_result, dict)
                and general_result.get("mode") == "general"
                and isinstance(generated_answer, str)
                and generated_answer.strip()
            ):
                english_answer = generated_answer.strip()
                reminder = "My main purpose is to help you learn about the Ganga, Namami Gange, and river conservation."
                if reminder.casefold() not in english_answer.casefold():
                    english_answer = f"{english_answer}\n\n{reminder}"
                mode = "general"
                if not cache_hit and cache_key:
                    self._general_response_cache.set(cache_key, {"answer": generated_answer.strip(), "mode": "general"})
            else:
                english_answer = GENERAL_GENERATION_FAILURE
                mode = "general-unavailable"

            # General output is generated in English and translated exactly once here.
            answer = translate_text(english_answer, "en", out_lang, allow_external=translation_consent)
            citations = []
            wants_sources = bool(re.search(r"\b(source|sources|citation|citations|reference|references|verify|verified|additional context)\b", cpcb_query, re.IGNORECASE))
            if mode == "general" and wants_sources:
                from integration.supplementary_info import append_supplementary_summaries

                summaries = self.external_source_service.search_summaries(cpcb_query, language=out_lang, max_sources=1)
                answer, external_citations = append_supplementary_summaries(answer, summaries)
                citations = [CitationItem(**item) for item in external_citations]
            usage = general_result.get("usage", {}) if isinstance(general_result, dict) else {}
            attempted_calls = usage.get("llm_calls", 0 if cache_hit else (1 if mode == "general" else 0))
            logger.info("general_response_cache cache_hit=%s llm_calls=%s", cache_hit, attempted_calls)
            pres = AvatarPresentation(
                state=ConversationState.SPEAKING,
                question=question,
                answer=answer,
                spoken_text=spoken_response(answer),
                mode=mode,
                citations=citations,
                input_language=in_lang,
                output_language=out_lang,
                language=out_lang,
                emotion=EmotionType.NEUTRAL,
                gesture=GestureType.EXPLAINING,
            )
            self._set_state(pres)
            return pres

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

        citations = list(brain_resp.citations)
        final_answer = brain_resp.answer
        source_request = bool(re.search(
            r"\b(source|sources|citation|citations|reference|references|verify|verified|additional context|compare|comparison|contrast|versus|vs\.?)\b",
            cpcb_query, re.IGNORECASE,
        ))
        if brain_resp.mode == "insufficient-evidence":
            from brain.answer_format import strip_answer_formatting_instructions
            from brain.retriever import is_broad_ganga_query

            overview_query = strip_answer_formatting_instructions(cpcb_query)
            if is_broad_ganga_query(overview_query):
                from integration.supplementary_info import append_supplementary_summaries

                summaries = self.external_source_service.search_summaries(
                    overview_query, language=out_lang, max_sources=1
                )
                if summaries:
                    limitation = translate_text(
                        "The verified project knowledge base did not provide enough evidence for a grounded answer. The following is separate external background:",
                        "en", out_lang, allow_external=translation_consent,
                    )
                    final_answer, external_citations = append_supplementary_summaries(
                        limitation, summaries
                    )
                    citations.extend(CitationItem(**item) for item in external_citations)
                    logger.info("Using bounded external background after an insufficient broad Ganga retrieval.")
        if brain_resp.mode == "grounded" and source_request:
            from integration.supplementary_info import append_supplementary_summaries

            summaries = self.external_source_service.search_summaries(cpcb_query, language=out_lang, max_sources=2)
            final_answer, external_citations = append_supplementary_summaries(final_answer, summaries)
            citations.extend(CitationItem(**item) for item in external_citations)

        # State 4: SPEAKING
        speaking_pres = AvatarPresentation(
            state=ConversationState.SPEAKING,
            question=question,
            answer=final_answer,
            spoken_text=spoken_response(final_answer),
            mode=brain_resp.mode,
            citations=citations,
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
