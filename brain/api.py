"""FastAPI HTTP API for frontend/avatar integration with Ganga Brain."""

from __future__ import annotations

import argparse
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .rag_pipeline import answer_question


app = FastAPI(
    title="Ganga AI Mascot Brain API",
    description="Verified Knowledge Base RAG API for Namami Gange awareness project",
    version="1.0.0",
)


class AskRequest(BaseModel):
    question: str = Field("", description="User question about River Ganga / GRBMP material", example="What are the major sources of pollution in the Ganga?")
    query: str | None = Field(None, description="Query alias for question")
    top_k: int | None = Field(None, description="Optional override for retriever top_k candidate count", example=5)

    def get_question(self) -> str:
        return (self.question or self.query or "").strip()


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


@app.get("/health")
def health():
    return {"status": "ok", "service": "ganga-brain-api"}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    q = req.get_question()
    if not q:
        raise HTTPException(status_code=400, detail="Question string must not be empty.")

    res = answer_question(q, top_k=req.top_k)
    return {
        "answer": res.get("answer", ""),
        "mode": res.get("mode", "insufficient-evidence"),
        "citations": res.get("citations", []),
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
