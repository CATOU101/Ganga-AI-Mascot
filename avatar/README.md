# Avatar and Browser Interface

This directory contains the active browser interface for the Ganga AI Mascot, including the Three.js Chacha Chaudhary character, chat controls, language selection, quiz UI, and supporting assets. The active page is `index.html`; `app.js` coordinates chat and browser speech, while `mascot.js` manages the rendered character and presentation state.

## Active interface

- The Three.js client loads the active Chacha model from `Chacha_New/` and presents Brain answers, citations, conversation state, and optional audio/lip-sync data.
- The quiz is implemented by `quiz.js` and `quiz-data.js`, with its interface initialized from the browser page.
- Text input/output selection supports English (`en`), Hindi (`hi`), Kannada (`kn`), and Tamil (`ta`). Translation is handled by the Brain and may send text to Google's public Translate endpoint; see the privacy notes in the [main README](../README.md#language-and-translation-privacy).
- Browser Web Speech recognition and synthesis locales are configured for those four languages. Actual locale support depends on the user's browser and its speech service.

## Voice capability boundary

Uploaded audio uses the integration STT adapter. Its Vosk model mapping supports English and Hindi only. Kannada/Tamil STT is rejected by the Vosk-backed route; browser locale selection is a separate provider-dependent path and does not establish Vosk support. Edge TTS voice identifiers are configured for all four languages, but live synthesis availability has not been validated across hosts. Windows SAPI fallback is configured only for English and Hindi. Rhubarb lip-sync uses a procedural cadence fallback when the bundled platform binary cannot run.

## Run locally

From the repository root, install dependencies as documented in the [main README](../README.md#installation-and-running), then start the integration service:

```bash
python -m integration.server --host 127.0.0.1 --port 8080
```

Open `http://127.0.0.1:8080/` when the integration service reports ready. See [integration documentation](../integration/README.md) for API routes and CPCB behavior.

The Unity and older avatar directories are retained historical or exploratory assets; the active web client is Three.js. The presence of assets and automated UI/asset tests does not establish a completed usability or educational-outcome evaluation.
