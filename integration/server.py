"""Unified Integration FastAPI server mounting Brain API, Integration endpoints, and Web Avatar UI."""

from __future__ import annotations

import argparse
import os
import uvicorn
from pathlib import Path
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from brain.api import app as brain_app
from integration.api.brain_client import BrainClient
from integration.config.integration_config import load_integration_config
from integration.controller.conversation_controller import ConversationController
from integration.models.brain_response import AvatarPresentation, BrainRequest
from integration.avatar.mascot_presenter import MascotPresenter
from integration.voice.stt_adapter import get_stt_adapter
from integration.voice.tts_adapter import get_tts_adapter

ROOT_DIR = Path(__file__).resolve().parents[1]
AVATAR_DIR = ROOT_DIR / "avatar"

config = load_integration_config()
brain_client = BrainClient(config)
controller = ConversationController(brain_client=brain_client, config=config)
presenter = MascotPresenter()
stt_adapter = get_stt_adapter(config.stt_provider)
tts_adapter = get_tts_adapter("synthetic" if config.mock_mode else config.tts_provider)

app = FastAPI(
    title="Ganga AI Mascot End-to-End Integration Server",
    description="Unified API & Avatar presentation server connecting Brain RAG, STT, TTS, Lip-Sync, and UI.",
    version="1.0.0",
)

# Enable CORS for local cross-origin connections (e.g., local Unity or WebGL app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/integration/health")
def integration_health():
    return {
        "status": "ok",
        "service": "ganga-integration-server",
        "mock_mode": config.mock_mode,
        "brain_url": config.brain_base_url,
    }


@app.post("/api/integration/ask", response_model=AvatarPresentation)
def integration_ask(req: BrainRequest):
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="Question string must not be empty.")

    # Process question through conversation state machine
    pres = controller.process_text_question(req.question, language=req.language)

    # Synthesize optional TTS audio & compute lip-sync frames
    tts_result = tts_adapter.synthesize_speech(pres.answer, language=req.language)
    final_pres = presenter.create_presentation(
        brain_response=brain_client.ask(req.question, language=req.language, top_k=req.top_k),
        conversation_state=pres.state,
        tts_result=tts_result
    )
    final_pres.question = req.question

    controller.finish_speaking(language=req.language)
    return final_pres


@app.post("/api/integration/stt", response_model=AvatarPresentation)
async def integration_stt(file: UploadFile = File(...), language: str = "hi"):
    audio_bytes = await file.read()
    transcription = stt_adapter.transcribe_audio(audio_bytes, language=language)

    if not transcription:
        return AvatarPresentation(
            state=controller.cancel_to_idle("Could not transcribe voice input.").state,
            answer="Sorry, I could not hear or transcribe your voice input.",
            mode="insufficient-evidence",
            language=language,
        )

    return integration_ask(BrainRequest(question=transcription, language=language))


# Mount the core Brain FastAPI router endpoints (/ask, /health) directly
app.mount("/brain", brain_app)

# Serve Web Mascot frontend if avatar directory exists
if AVATAR_DIR.exists() and (AVATAR_DIR / "index.html").exists():
    app.mount("/", StaticFiles(directory=str(AVATAR_DIR), html=True), name="avatar_ui")


def main():
    parser = argparse.ArgumentParser(description="Start Ganga AI Mascot Integration Server")
    parser.add_argument("--host", default=config.server_host, help="Host address to bind")
    parser.add_argument("--port", type=int, default=config.server_port, help="Port to listen on")
    args = parser.parse_args()

    uvicorn.run("integration.server:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
