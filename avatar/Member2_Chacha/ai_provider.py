"""
Chacha Chaudhary - AI Provider Abstraction Layer
Stage 12B: Clean Interface for Member 1 AI & Development Mock

Architecture:
    BaseAIProvider (ABC)
      ├── Member1AIProvider (Production adapter stub, awaiting Member 1 specification)
      └── MockAIProvider (DEVELOPMENT-ONLY mock for end-to-end pipeline validation)

Contract:
    All providers return a dictionary:
    {
        "response_text": str,
        "language": str,              # "en" or "hi"
        "emotion": Optional[str],     # "happy", "thinking", or None
        "emotion_intensity": float,   # 0.0 to 1.0
        "body_action": Optional[str]  # "Chacha_Nod", etc., or None
    }
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class AIProviderError(Exception):
    """Base exception for AI provider errors."""
    pass


class Member1AIEngineUnavailableError(AIProviderError):
    """Raised when Member 1 AI API endpoint is not yet connected or configured."""
    pass


class EmptyAIResponseError(AIProviderError):
    """Raised when AI response text is empty."""
    pass


class BaseAIProvider(ABC):
    """Abstract Base Class for AI Response Providers."""

    @abstractmethod
    def respond(self, text: str, language: str = "en") -> Dict[str, Any]:
        """
        Processes user query text and generates an avatar response.
        
        Args:
            text: Input user speech/query.
            language: 'en' for English, 'hi' for Hindi.
            
        Returns:
            Dict containing response_text, language, emotion, emotion_intensity, body_action.
        """
        pass


class Member1AIProvider(BaseAIProvider):
    """
    Adapter and placeholder interface for Member 1's RAG/AI Reasoning Engine.
    
    IMPORTANT:
    This class is an unconfigured production interface stub.
    It deliberately does NOT invent fake URLs, ports, auth tokens, or payload schemas.
    When Member 1 supplies the endpoint specification, configure it via initialize().
    """

    def __init__(self, endpoint_url: Optional[str] = None, api_key: Optional[str] = None):
        self.endpoint_url = endpoint_url
        self.api_key = api_key

    def respond(self, text: str, language: str = "en") -> Dict[str, Any]:
        if not self.endpoint_url:
            raise Member1AIEngineUnavailableError(
                "Member 1 AI API endpoint is not configured. "
                "Specification pending from Member 1 team. "
                "Use MockAIProvider for local offline pipeline testing."
            )
        # Production HTTP/WebSocket client will be wired here once Member 1 provides contract
        raise NotImplementedError("Member 1 network client awaiting API contract.")


class MockAIProvider(BaseAIProvider):
    """
    DEVELOPMENT-ONLY Mock AI Provider.
    
    WARNING:
    This class provides deterministic offline responses solely for testing the
    multimodal chain (STT -> AI -> TTS -> Rhubarb -> AvatarController).
    It is NOT Member 1 AI.
    """

    DEVELOPMENT_DISCLAIMER = "DEVELOPMENT-ONLY MOCK AI FOR PIPELINE VALIDATION. NOT MEMBER 1 AI."

    # Contextual knowledge responses for Chacha persona
    PRESET_RESPONSES = {
        "en": {
            "hello": "Hello! I am doing great. Chacha's brain works faster than a computer!",
            "default": "Chacha Chaudhary is always here to help you solve any problem with wisdom!"
        },
        "hi": {
            "नमस्ते": "नमस्ते बेटा! चाचा चौधरी का दिमाग कंप्यूटर से भी तेज़ चलता है!",
            "default": "चाचा चौधरी हमेशा समझदारी और सूझबूझ से हर मुश्किल हल कर देते हैं!"
        }
    }

    def __init__(self, default_emotion: Optional[str] = "happy", default_intensity: float = 0.8, default_body_action: Optional[str] = "Chacha_Nod"):
        self.default_emotion = default_emotion
        self.default_intensity = default_intensity
        self.default_body_action = default_body_action

    def respond(self, text: str, language: str = "en") -> Dict[str, Any]:
        lang_key = str(language).lower().strip()
        if not text or not text.strip():
            raise EmptyAIResponseError("Cannot generate response for empty input text.")

        clean_input = text.strip()

        # Match contextual responses
        if lang_key == "hi":
            if any(k in clean_input for k in ["नमस्ते", "प्रणाम", "चाचा", "कैसे"]):
                resp_text = self.PRESET_RESPONSES["hi"]["नमस्ते"]
            else:
                resp_text = self.PRESET_RESPONSES["hi"]["default"]
            emotion = "happy"
            intensity = 0.8
            body_act = "Chacha_Nod"

        else:  # English
            lower_input = clean_input.lower()
            if any(k in lower_input for k in ["hello", "chacha", "how are you", "hi"]):
                resp_text = self.PRESET_RESPONSES["en"]["hello"]
            else:
                resp_text = self.PRESET_RESPONSES["en"]["default"]
            emotion = "happy"
            intensity = 0.8
            body_act = "Chacha_Nod"

        return {
            "response_text": resp_text,
            "language": lang_key,
            "emotion": emotion,
            "emotion_intensity": intensity,
            "body_action": body_act,
            "is_mock": True,
            "disclaimer": self.DEVELOPMENT_DISCLAIMER
        }
