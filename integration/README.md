# Integration

The integration FastAPI application connects the existing chat and voice flows to the Brain API and serves the avatar client. CPCB live water-quality questions are intercepted in the conversation controller before the Brain/RAG request; all other questions continue through the existing path.

For live water-quality requests, the server retrieves the CPCB station registry and layer-10 snapshot from:

- `https://rtwqmsdb1.cpcb.gov.in/data/internet/stations/stations.json`
- `https://rtwqmsdb1.cpcb.gov.in/data/internet/layers/10/index.json`

The chat response uses verified station mappings for Haridwar (UK55 / station 11788), Kanpur (UT58 / 11791), Ghazipur (UT66 / 11798), Farakka (WB86 / 11815), and Nabadwip (WB87 / 11816). A quality request returns a separate table with exactly pH, BOD, and DO; an explicit location limits the rows to that station, and an unspecified location returns all five. Combined requests return separate quality and water-level/depth tables. The live layer-10 snapshot was checked for all five configured stations and currently identifies river stage as `stationparameter_no=S`, `stationparameter_longname=River Stage`, unit `m`, and depth as `stationparameter_no=Depth`, `stationparameter_longname=Depth`, unit `m`. Quality codes are pH (`---`), BOD (`mg/l`), and DO (`mg/l`). Parameter availability and units come from the CPCB payload; missing values display as `N/A`. Tables include per-reading CPCB timestamps, freshness labels, station IDs, and source attribution. The server caches successful source payloads for 60 seconds. Reading freshness is determined from the CPCB measurement timestamp, independently of cache age; measurements older than 90 minutes are labelled stale.

Responses render structured tables directly in the chatbot, with CPCB attribution, raw values, units, timestamps, status, and the criterion used. Water-quality statuses use CPCB's published Designated Best Use Class B organized outdoor-bathing criteria (pH 6.5–8.5, DO at least 5 mg/L, BOD 5-day/20°C at most 3 mg/L): https://cpcb.nic.in/wqm/Designated_Best_Use_Water_Quality_Criteria.pdf. BOD status is unavailable unless the measurement explicitly identifies the matching method/basis; the live CPCB feed does not currently provide it. Stale, missing, nonnumeric, or unit-incompatible readings also have unavailable status. Class B is a bathing-use benchmark; these three readings alone do not establish overall water safety or suitability. CWC thresholds are station-specific (official reference: https://cwc.gov.in/sites/default/files/sopapril2025.pdf); the implementation does not have a verified exact CPCB-to-CWC gauge match and current threshold feed, so river-stage status remains unavailable, with the CWC Flood Forecasting portal cited for reference: https://ffs.india-water.gov.in/. CPCB's separate `Depth` reading remains visible but is not derived from stage and has no verified threshold. The CPCB terms for reuse have not been independently verified and should be reviewed before publication or wider redistribution.

Text language controls support `en`, `hi`, `kn`, and `ta`. Input detection is Unicode-script heuristic; explicit language values take precedence. When a language conversion is needed, external translation to Google's public Translate endpoint is enabled by default and may send the question and/or generated answer. The endpoint's specific terms and retention have not been verified; do not send personal or confidential text. API callers can set `translation_consent=false` to disable external translation for a request. Exact built-in system phrases can be translated locally; no raw-text translation cache is retained. CPCB readings still use the dedicated CPCB path; if external translation is disabled or fails, readings remain in English with an explanatory note.

Vosk currently has configured English and Hindi speech models only. Kannada/Tamil browser speech locale selection is configuration only; actual recognition depends on browser support. Edge TTS voice identifiers are configured for all four languages, but availability has not been systematically checked across language/host combinations; Windows SAPI fallback is configured only for English/Hindi.

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
