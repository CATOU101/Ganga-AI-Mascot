"""FastAPI HTTP API for frontend/avatar integration with Ganga Brain."""

from __future__ import annotations

import argparse
import logging
from typing import Literal

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field

from .config import MAX_API_TOP_K, load_config
from .rag_pipeline import answer_question
from .translator import TranslationError
from .vector_store import get_vector_store


logger = logging.getLogger("brain.api")


app = FastAPI(
    title="Ganga AI Mascot Brain API",
    description="Reviewed Knowledge Base RAG API for Namami Gange awareness project",
    version="1.0.0",
)


class AskRequest(BaseModel):
    question: str = Field(..., description="User question about River Ganga / GRBMP material", example="What are the major sources of pollution in the Ganga?")
    input_language: Literal["en", "hi"] | None = Field(None, description="Input language ('en' | 'hi')", example="en")
    output_language: Literal["en", "hi"] | None = Field(None, description="Output language ('en' | 'hi')", example="en")
    language: Literal["en", "hi"] | None = Field(None, description="Legacy language fallback ('en' | 'hi')")
    top_k: int | None = Field(
        None,
        ge=1,
        le=MAX_API_TOP_K,
        description="Maximum number of reranked evidence results returned (default from Brain configuration).",
        example=5,
    )

    def get_input_language(self) -> str:
        if self.input_language:
            return self.input_language.lower().strip()
        if self.language:
            return self.language.lower().strip()
        return "en"

    def get_output_language(self) -> str:
        if self.output_language:
            return self.output_language.lower().strip()
        if self.language:
            return self.language.lower().strip()
        return self.get_input_language()


class CitationItem(BaseModel):
    source: str | None = Field(None, description="Document title")
    file_name: str | None = Field(None, description="Source PDF file name")
    page: str | None = Field(None, description="Page number or range")
    section: str | None = Field(None, description="Section title or ID")
    knowledge_type: str | None = Field(None, description="Classification context: HISTORICAL, METHODOLOGICAL, etc.")


class AskResponse(BaseModel):
    answer: str = Field(..., description="Grounded answer text or safe fallback message")
    mode: str = Field(..., description="Response mode: 'grounded' | 'insufficient-evidence' | 'current-info-fallback'")
    citations: list[CitationItem] = Field(default_factory=list, description="Traceable provenance citations")
    input_language: str = Field("en", description="Input language code")
    output_language: str = Field("en", description="Output language code")


@app.get("/health")
def health(response: Response):
    try:
        store = get_vector_store(load_config())
        store.check_embedding_ready()
    except Exception as exc:
        logger.exception("Brain readiness check failed")
        response.status_code = 503
        return {
            "status": "not_ready",
            "service": "ganga-brain-api",
            "application": "available",
            "brain": {"ready": False, "reason": type(exc).__name__},
        }

    return {
        "status": "ok",
        "service": "ganga-brain-api",
        "application": "available",
        "brain": {"ready": True, "collection": store.config.collection_name, "chunks": store.count()},
    }


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="Question string must not be empty.")

    in_lang = req.get_input_language()
    out_lang = req.get_output_language()
    try:
        res = answer_question(
            req.question,
            top_k=req.top_k,
            input_language=in_lang,
            output_language=out_lang,
        )
    except TranslationError as exc:
        raise HTTPException(status_code=503, detail="Requested answer translation is unavailable.") from exc
    return {
        "answer": res.get("answer", ""),
        "mode": res.get("mode", "insufficient-evidence"),
        "citations": res.get("citations", []),
        "input_language": in_lang,
        "output_language": out_lang,
    }


def main():
    import uvicorn

    parser = argparse.ArgumentParser(description="Start Ganga Brain API server")
    parser.add_argument("--host", default="0.0.0.0", help="Host address to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    args = parser.parse_args()

    uvicorn.run("brain.api:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
