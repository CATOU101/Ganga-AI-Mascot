"""Robust HTTP client for communication with Ganga AI Brain API."""

from __future__ import annotations

import logging
import json
import urllib.request
import urllib.error
from typing import Any

from integration.config.integration_config import IntegrationConfig, load_integration_config
from integration.models.brain_response import BrainRequest, BrainResponse, CitationItem, EmotionType, GestureType

logger = logging.getLogger("integration.brain_client")


class BrainClientError(Exception):
    """Base exception for Brain client communication failures."""
    pass


class BrainConnectionError(BrainClientError):
    """Raised when connection to Brain API fails or times out."""
    pass


class BrainResponseError(BrainClientError):
    """Raised when Brain API returns HTTP error or malformed payload."""
    pass


class BrainClient:
    def __init__(self, config: IntegrationConfig | None = None) -> None:
        self.config = config or load_integration_config()

    def ask(self, question: str, language: str = "hi", top_k: int | None = None) -> BrainResponse:
        """Send question to Brain API POST /ask safely."""
        if not question or not question.strip():
            logger.warning("[Integration] Empty question provided to BrainClient.")
            return self._fallback_response(
                answer="Please ask a question about River Ganga or Namami Gange programs.",
                mode="insufficient-evidence",
                language=language
            )

        if self.config.mock_mode:
            logger.info("[Integration] MOCK_MODE active. Returning mock Brain response.")
            return self._mock_response(question, language)

        url = f"{self.config.brain_base_url}/ask"
        payload = {
            "question": question.strip(),
            "language": language,
        }
        if top_k is not None:
            payload["top_k"] = top_k

        data = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        logger.info(f"[Integration] Sending question to Brain API at {url}")

        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        
        try:
            with urllib.request.urlopen(req, timeout=self.config.brain_timeout_seconds) as response:
                status_code = response.status
                if status_code != 200:
                    raise BrainResponseError(f"Brain API returned HTTP status {status_code}")
                
                resp_bytes = response.read()
                return self._parse_response(resp_bytes, language)

        except (urllib.error.URLError, TimeoutError, OSError) as e:
            logger.info(f"[Integration] Standalone Brain HTTP server unreachable ({e}). Calling RAG pipeline in-process.")
            try:
                from brain.rag_pipeline import answer_question
                rag_res = answer_question(question.strip(), top_k=top_k)
                mode = rag_res.get("mode", "insufficient-evidence")
                gesture = "explaining" if mode == "grounded" else ("thinking" if mode == "insufficient-evidence" else "idle")
                return self._parse_response(
                    json.dumps({
                        "answer": rag_res.get("answer", ""),
                        "mode": mode,
                        "citations": rag_res.get("citations", []),
                        "language": language,
                        "emotion": "neutral",
                        "gesture": gesture,
                    }).encode("utf-8"),
                    language
                )
            except Exception as in_proc_err:
                logger.error(f"[Integration] In-process RAG execution error: {in_proc_err}")
                return self._fallback_response(
                    answer="Sorry, I am having trouble connecting to the Ganga AI Brain right now. Please check if the Brain server is running.",
                    mode="insufficient-evidence",
                    language=language
                )

        except Exception as e:
            logger.error(f"[Integration] Unexpected error in BrainClient: {e}")
            return self._fallback_response(
                answer="An unexpected error occurred while processing your query.",
                mode="insufficient-evidence",
                language=language
            )

    def _parse_response(self, raw_bytes: bytes, request_language: str) -> BrainResponse:
        """Parse JSON response safely with full validation and fallback defaults."""
        try:
            data = json.loads(raw_bytes.decode("utf-8"))
        except Exception as err:
            logger.error(f"[Integration] Malformed JSON received from Brain API: {err}")
            return self._fallback_response(
                answer="Received an invalid response format from the AI Brain server.",
                mode="insufficient-evidence",
                language=request_language
            )

        if not isinstance(data, dict):
            return self._fallback_response("Invalid response format.", "insufficient-evidence", request_language)

        answer = str(data.get("answer", "")).strip() or "No response available."
        mode = str(data.get("mode", "insufficient-evidence"))
        language = str(data.get("language") or request_language)
        
        # Parse citations safely
        raw_citations = data.get("citations", [])
        citations: list[CitationItem] = []
        if isinstance(raw_citations, list):
            for item in raw_citations:
                if isinstance(item, dict):
                    citations.append(CitationItem(
                        source=item.get("source"),
                        file_name=item.get("file_name"),
                        page=str(item.get("page", "")) if item.get("page") is not None else None,
                        section=item.get("section"),
                        knowledge_type=item.get("knowledge_type")
                    ))

        # Parse emotion & gesture safely
        raw_emotion = str(data.get("emotion", "neutral")).lower()
        raw_gesture = str(data.get("gesture", "idle")).lower()

        try:
            emotion = EmotionType(raw_emotion)
        except ValueError:
            emotion = EmotionType.NEUTRAL

        try:
            gesture = GestureType(raw_gesture)
        except ValueError:
            gesture = GestureType.IDLE

        return BrainResponse(
            answer=answer,
            mode=mode,
            citations=citations,
            language=language,
            emotion=emotion,
            gesture=gesture,
        )

    def _fallback_response(self, answer: str, mode: str, language: str) -> BrainResponse:
        return BrainResponse(
            answer=answer,
            mode=mode,
            citations=[],
            language=language,
            emotion=EmotionType.NEUTRAL,
            gesture=GestureType.IDLE
        )

    def _mock_response(self, question: str, language: str) -> BrainResponse:
        """Generate a realistic mock response for testing without backend."""
        q_lower = question.lower()
        if "aviral" in q_lower or "dhara" in q_lower:
            return BrainResponse(
                answer="Aviral Dhara refers to the continuous flow requirement of River Ganga. Under GRBMP recommendations, maintaining ecological flow (e-flow) is vital for river health, ecological balance, and water quality.",
                mode="grounded",
                citations=[
                    CitationItem(
                        source="GRBMP Ecological Flow Report",
                        file_name="001_GRBMP_EFlows.pdf",
                        page="12-18",
                        section="Section 3: River Connectivity",
                        knowledge_type="METHODOLOGICAL"
                    )
                ],
                language=language,
                emotion=EmotionType.NEUTRAL,
                gesture=GestureType.EXPLAINING
            )
        elif "mars" in q_lower:
            return BrainResponse(
                answer="The retrieved Ganga River Basin Management Plan (GRBMP) material does not contain sufficient evidence to answer questions about Mars.",
                mode="insufficient-evidence",
                citations=[],
                language=language,
                emotion=EmotionType.THINKING,
                gesture=GestureType.THINKING
            )
        else:
            return BrainResponse(
                answer=f"Mock response for query: '{question}'. Ganga river conservation emphasizes community participation (River-People Connect) and industrial effluent regulation.",
                mode="grounded",
                citations=[
                    CitationItem(
                        source="Namami Gange Overview",
                        file_name="002_NMCG_Vision.pdf",
                        page="5-9",
                        section="Section 1: Vision",
                        knowledge_type="GENERAL"
                    )
                ],
                language=language,
                emotion=EmotionType.HAPPY,
                gesture=GestureType.WAVE
            )
