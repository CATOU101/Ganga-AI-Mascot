# Integration

The integration FastAPI application connects the existing chat and voice flows to the Brain API and serves the avatar client. CPCB live water-quality questions are intercepted in the conversation controller before the Brain/RAG request; all other questions continue through the existing path.

For live water-quality requests, the server retrieves the CPCB station registry and layer-10 snapshot from:

- `https://rtwqmsdb1.cpcb.gov.in/data/internet/stations/stations.json`
- `https://rtwqmsdb1.cpcb.gov.in/data/internet/layers/10/index.json`

The chat response uses verified station mappings for Haridwar (UK55 / station 11788), Kanpur (UT58 / 11791), Ghazipur (UT66 / 11798), Farakka (WB86 / 11815), and Nabadwip (WB87 / 11816). A quality request returns a separate table with exactly pH, BOD, and DO; an explicit location limits the rows to that station, and an unspecified location returns all five. Combined requests return separate quality and water-level/depth tables. The live layer-10 snapshot was checked for all five configured stations and currently identifies river stage as `stationparameter_no=S`, `stationparameter_longname=River Stage`, unit `m`, and depth as `stationparameter_no=Depth`, `stationparameter_longname=Depth`, unit `m`. Quality codes are pH (`---`), BOD (`mg/l`), and DO (`mg/l`). Parameter availability and units come from the CPCB payload; missing values display as `N/A`. Tables include per-reading CPCB timestamps, freshness labels, station IDs, and source attribution. The server caches successful source payloads for 60 seconds. Reading freshness is determined from the CPCB measurement timestamp, independently of cache age; measurements older than 90 minutes are labelled stale.

Responses render structured tables directly in the chatbot, with CPCB attribution, raw values, units, timestamps, status, and the criterion used. Water-quality statuses use CPCB's published Designated Best Use Class B organized outdoor-bathing criteria (pH 6.5–8.5, DO at least 5 mg/L, BOD 5-day/20°C at most 3 mg/L): https://cpcb.nic.in/wqm/Designated_Best_Use_Water_Quality_Criteria.pdf. BOD status is unavailable unless the measurement explicitly identifies the matching method/basis; the live CPCB feed does not currently provide it. Stale, missing, nonnumeric, or unit-incompatible readings also have unavailable status. Class B is a bathing-use benchmark; these three readings alone do not establish overall water safety or suitability. CWC thresholds are station-specific (official reference: https://cwc.gov.in/sites/default/files/sopapril2025.pdf); the implementation does not have a verified exact CPCB-to-CWC gauge match and current threshold feed, so river-stage status remains unavailable, with the CWC Flood Forecasting portal cited for reference: https://ffs.india-water.gov.in/. CPCB's separate `Depth` reading remains visible but is not derived from stage and has no verified threshold. The CPCB terms for reuse have not been independently verified and should be reviewed before publication or wider redistribution.

Text input/output supports `en`, `hi`, `kn`, `ta`, `te`, `bn`, `mr`, `gu`, `ml`, `pa`, `ur`, `or`, and `as`. Detection uses Unicode script with heuristic disambiguation for shared-script language pairs; short ambiguous Hindi/Marathi or Bengali/Assamese text can be uncertain. Non-English input is translated before RAG retrieval and, when applicable, before CPCB intent/station matching. Responses and CPCB table headers/statuses are translated/localized while numeric readings, units, timestamps and citations remain structured. The default public Google Translate endpoint is undocumented. Set `GOOGLE_TRANSLATE_API_KEY` to use documented Google Cloud Translation REST; it requires a Google Cloud project and billing after its free monthly allowance. External translation sends user text to Google by default; callers can set `translation_consent=false` to disable it. No raw-text translation cache is retained.

Speech input/output has configured mappings for all 13 supported languages through Azure Speech. Install optional `requirements-speech.txt`, then provide `AZURE_SPEECH_KEY` and `AZURE_SPEECH_REGION`; `STT_PROVIDER=auto` prefers Azure when configured, then Vosk (English/Hindi only), else reports that recognition is unavailable. The SDK is covered by Microsoft's Software License Terms (PyPI lists Other/Proprietary); review the [license](https://aka.ms/csspeech/license). The frontend includes a separate microphone input selector and uses browser Web Speech only as a device-dependent path. Azure service use may incur charges; see Microsoft's current [Speech pricing](https://azure.microsoft.com/en-in/pricing/details/speech/) and [quotas](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/speech-services-quotas-and-limits). Edge TTS supplies a no-key online fallback using a community LGPL-3.0 client, with no SLA; SAPI is English-only. Provider mappings and mocked contract tests do not establish real-recorder recognition accuracy or natural pronunciation for each language.

Run the deterministic mocked route tests and the dependency-free table-renderer tests with:

```bash
python -m pytest -q integration/tests/test_water_quality_chat.py
node --test avatar/tests/cpcb-tables.test.js
```

## Run the integration service

From the repository root, start the combined integration and avatar service with:

```bash
python -m integration.server --host 127.0.0.1 --port 8080
```

The server provides `/api/integration/health`, `/api/integration/ask`, and `/api/integration/stt`, mounts the Brain API under `/brain`, and serves `avatar/` at `/` when available. The in-process integration path calls the Brain pipeline directly; a separately launched Brain process loads its own project-root environment configuration. Run the mocked integration regression suite with `./.venv/bin/python -m pytest -q integration/tests --ignore=integration/tests/test_end_to_end.py` when dependencies are installed. The end-to-end module may make network-dependent translation calls.

The CPCB path covers a limited station/parameter set, not a river-wide sensor network. Its current upstream availability and the service's reuse terms were not independently confirmed during this documentation audit.
