# Integration

The integration FastAPI application connects the existing chat and voice flows to the Brain API and serves the avatar client. CPCB live water-quality questions are intercepted in the conversation controller before the Brain/RAG request; all other questions continue through the existing path.

For live water-quality requests, the server retrieves the CPCB station registry and layer-10 snapshot from:

- `https://rtwqmsdb1.cpcb.gov.in/data/internet/stations/stations.json`
- `https://rtwqmsdb1.cpcb.gov.in/data/internet/layers/10/index.json`

The chat response uses verified station mappings for Haridwar (UK55 / station 11788), Kanpur (UT58 / 11791), Ghazipur (UT66 / 11798), Farakka (WB86 / 11815), and Nabadwip (WB87 / 11816). The default overview requests DO, BOD, and pH at all five locations; explicit station/parameter requests are limited to those selections. The server caches successful source payloads for 60 seconds. Reading freshness is determined from the CPCB measurement timestamp, independently of cache age; measurements older than 90 minutes are labelled stale.

Responses are ordinary chatbot messages, attributed to the CPCB Real-Time Water Quality Monitoring System, with a disclaimer that point readings apply to a particular station and time and do not by themselves determine drinking-water safety. The CPCB terms for reuse have not been independently verified and should be reviewed before publication or wider redistribution.

Run the deterministic mocked tests with:

```bash
python -m pytest -q integration/tests/test_water_quality_chat.py
```
