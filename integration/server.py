"""Unified Integration FastAPI server mounting Brain API, Integration endpoints, and Web Avatar UI."""

from __future__ import annotations

import argparse
import os
import time
import logging
logger = logging.getLogger("integration.server")
import uvicorn
from pathlib import Path
from fastapi import FastAPI, HTTPException, File, UploadFile, Response
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


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(content=b"", media_type="image/x-icon", status_code=204)


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
    t0 = time.perf_counter()
    q_text = req.get_question()
    if not q_text:
        raise HTTPException(status_code=400, detail="Question string must not be empty.")

    in_lang = req.get_input_language()
    out_lang = req.get_output_language()
    t1 = time.perf_counter()

    # T2: Brain/RAG start
    t2 = time.perf_counter()
    pres = controller.process_text_question(q_text, input_language=in_lang, output_language=out_lang, top_k=req.top_k)
    t5 = time.perf_counter()

    # T6: TTS synthesis
    t6 = time.perf_counter()
    tts_result = tts_adapter.synthesize_speech(pres.answer, language=out_lang)
    t7 = time.perf_counter()

    # T8: Rhubarb lip-sync analysis
    t8 = time.perf_counter()
    final_pres = presenter.attach_audio_and_lipsync(pres, tts_result=tts_result)
    t9 = time.perf_counter()

    final_pres.question = q_text
    controller.finish_speaking(input_language=in_lang, output_language=out_lang)
    t10 = time.perf_counter()

    timing_info = {
        "t0_received": round(t0, 4),
        "t1_validation_ms": round((t1 - t0) * 1000, 2),
        "t2_rag_start_ms": round((t2 - t0) * 1000, 2),
        "t3_to_t5_brain_ms": round((t5 - t2) * 1000, 2),
        "t6_tts_start_ms": round((t6 - t0) * 1000, 2),
        "t7_tts_ms": round((t7 - t6) * 1000, 2),
        "t8_rhubarb_start_ms": round((t8 - t0) * 1000, 2),
        "t9_rhubarb_ms": round((t9 - t8) * 1000, 2),
        "t10_serialization_ms": round((t10 - t9) * 1000, 2),
        "total_backend_ms": round((t10 - t0) * 1000, 2),
    }
    final_pres.timing = timing_info

    logger.info(
        f"[PIPELINE LATENCY] Total: {timing_info['total_backend_ms']}ms | "
        f"Validation: {timing_info['t1_validation_ms']}ms | "
        f"Brain RAG: {timing_info['t3_to_t5_brain_ms']}ms | "
        f"TTS: {timing_info['t7_tts_ms']}ms | "
        f"Rhubarb: {timing_info['t9_rhubarb_ms']}ms"
    )
    print(
        f"[PIPELINE LATENCY] Total: {timing_info['total_backend_ms']}ms | "
        f"RAG: {timing_info['t3_to_t5_brain_ms']}ms | "
        f"TTS: {timing_info['t7_tts_ms']}ms | "
        f"Rhubarb: {timing_info['t9_rhubarb_ms']}ms",
        flush=True
    )
    return final_pres


@app.post("/api/integration/stt", response_model=AvatarPresentation)
async def integration_stt(
    file: UploadFile = File(None),
    audio: UploadFile = File(None),
    input_language: str = "hi",
    output_language: str = "hi",
    language: str | None = None,
):
    upload_file = file or audio
    if not upload_file:
        raise HTTPException(status_code=400, detail="Audio file must be uploaded as 'file' or 'audio'.")

    in_lang = (input_language or language or "hi").lower().strip()
    out_lang = (output_language or language or "hi").lower().strip()

    audio_bytes = await upload_file.read()
    transcription = stt_adapter.transcribe_audio(audio_bytes, language=in_lang)

    if not transcription:
        return AvatarPresentation(
            state=controller.cancel_to_idle("Could not transcribe voice input.").state,
            answer="Sorry, I could not hear or transcribe your voice input.",
            mode="insufficient-evidence",
            input_language=in_lang,
            output_language=out_lang,
            language=out_lang,
        )

    return integration_ask(BrainRequest(question=transcription, input_language=in_lang, output_language=out_lang))


# Mount the core Brain FastAPI router endpoints (/ask, /health) directly
app.mount("/brain", brain_app)

@app.on_event("startup")
def startup_warmup():
    try:
        from brain.config import load_config
        from brain.retriever import Retriever
        cfg = load_config()
        r = Retriever(cfg)
        r.retrieve("warmup query", top_k=1)
        print("[Startup] Vector Store and ONNX embeddings pre-warmed successfully.", flush=True)
    except Exception as e:
        print(f"[Startup] Warmup warning: {e}", flush=True)


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
