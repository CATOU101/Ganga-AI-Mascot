# Integration

The integration FastAPI application connects the existing chat and voice flows to the Brain API and serves the avatar client. CPCB live water-quality questions are intercepted in the conversation controller before the Brain/RAG request; all other questions continue through the existing path.

For live water-quality requests, the server retrieves the CPCB station registry and layer-10 snapshot from:

- `https://rtwqmsdb1.cpcb.gov.in/data/internet/stations/stations.json`
- `https://rtwqmsdb1.cpcb.gov.in/data/internet/layers/10/index.json`

The chat response uses verified station mappings for Haridwar (UK55 / station 11788), Kanpur (UT58 / 11791), Ghazipur (UT66 / 11798), Farakka (WB86 / 11815), and Nabadwip (WB87 / 11816). The default overview requests DO, BOD, and pH at all five locations; explicit station/parameter requests are limited to those selections. The server caches successful source payloads for 60 seconds. Reading freshness is determined from the CPCB measurement timestamp, independently of cache age; measurements older than 90 minutes are labelled stale.

Responses are ordinary chatbot messages, attributed to the CPCB Real-Time Water Quality Monitoring System, with a disclaimer that point readings apply to a particular station and time and do not by themselves determine drinking-water safety. The CPCB terms for reuse have not been independently verified and should be reviewed before publication or wider redistribution.

Text language controls support `en`, `hi`, `kn`, and `ta`. Input detection is Unicode-script heuristic; explicit language values take precedence. When a language conversion is needed, external translation to Google's public Translate endpoint is enabled by default and may send the question and/or generated answer. The endpoint's specific terms and retention have not been verified; do not send personal or confidential text. API callers can set `translation_consent=false` to disable external translation for a request. Exact built-in system phrases can be translated locally; no raw-text translation cache is retained. CPCB readings still use the dedicated CPCB path; if external translation is disabled or fails, readings remain in English with an explanatory note.

Vosk currently has configured English and Hindi speech models only. Kannada/Tamil browser speech locale selection is configuration only; actual recognition depends on browser support. Edge TTS voice identifiers are configured for all four languages, but live synthesis availability has not been smoke-tested; Windows SAPI fallback is only configured for English/Hindi.

Run the deterministic mocked tests with:

```bash
python -m pytest -q integration/tests/test_water_quality_chat.py
```
