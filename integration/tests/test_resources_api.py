from fastapi import FastAPI
from fastapi.testclient import TestClient

from integration import resources_api
from integration.resource_catalog import ResourceCatalog


def _metadata(**overrides):
    values = {
        "section_id": "approved-section-1",
        "source_id": "GRBMP-TEST-1",
        "file_name": "sample-report.pdf",
        "title": "Sample Ganga Report",
        "section": "River Overview",
        "subsection": "Course",
        "page_start": 4,
        "page_end": 5,
        "section_classification": "KEEP",
        "knowledge_type": "STATIC",
        "time_period": "Static reference in the approved report.",
        "geographic_scope": "Ganga River Basin",
        "relevance": "An approved introductory section.",
    }
    values.update(overrides)
    return values


def _catalog():
    chunks = [
        {
            "chunk_id": "approved-section-1::chunk-001",
            "text": "The Ganga begins at Gaumukh. Its course is long.",
            "metadata": _metadata(),
        },
        {
            "chunk_id": "approved-section-1::chunk-002",
            "text": "Its course is long. It reaches Ganga Sagar.",
            "metadata": _metadata(),
        },
        {
            "chunk_id": "approved-section-2::chunk-001",
            "text": "Historical river information.",
            "metadata": _metadata(
                section_id="approved-section-2",
                section="Historical Notes",
                section_classification="KEEP_HISTORICAL",
                knowledge_type="HISTORICAL",
                page_start=6,
                page_end=7,
            ),
        },
        {
            "chunk_id": "other-document::chunk-001",
            "text": "An ecological section.",
            "metadata": _metadata(
                section_id="approved-section-3",
                file_name="another-report.pdf",
                title="Another Report",
                section="Ecological Notes",
                page_start=1,
                page_end=1,
            ),
        },
    ]
    return ResourceCatalog(chunks, overlap_chars=19)


def test_catalog_groups_chunks_by_document_and_section_and_removes_overlap():
    catalog = _catalog()
    result = catalog.get_document("sample-report.pdf")

    assert result is not None
    assert result["section_count"] == 2
    overview = next(section for section in result["sections"] if section["section"] == "River Overview")
    assert overview["text"] == "The Ganga begins at Gaumukh. Its course is long.\n\nIt reaches Ganga Sagar."
    assert overview["page_start"] == 4
    assert overview["page_end"] == 5
    assert overview["source_id"] == "GRBMP-TEST-1"
    assert {section["knowledge_type"] for section in result["sections"]} == {"STATIC", "HISTORICAL"}
    assert catalog.document_list()["counts"] == {
        "documents": 2, "approved_sections": 3, "indexed_chunks": 4,
    }


def test_search_returns_source_excerpt_without_index_or_vector_internals():
    results = _catalog().search("Gaumukh", limit=5)
    assert len(results) == 1
    result = results[0]
    assert result["excerpt"] == "The Ganga begins at Gaumukh. Its course is long.\n\nIt reaches Ganga Sagar."
    assert result["file_name"] == "sample-report.pdf"
    assert result["page_start"] == 4
    assert "chunk_id" not in result
    assert "section_id" not in result
    assert "vector" not in result


def test_resources_routes_list_search_document_and_404(monkeypatch):
    app = FastAPI()
    app.include_router(resources_api.router)
    monkeypatch.setattr(resources_api, "get_resource_catalog", _catalog)
    client = TestClient(app)

    listing = client.get("/api/integration/resources").json()
    assert listing["counts"] == {"documents": 2, "approved_sections": 3, "indexed_chunks": 4}
    assert "sections" not in listing["documents"][0]
    assert client.get("/api/integration/resources/search", params={"q": "Gaumukh"}).json()["results"]
    document = client.get(
        "/api/integration/resources/document", params={"file_name": "sample-report.pdf"}
    )
    assert document.status_code == 200
    assert document.json()["sections"][0]["text"]
    assert client.get(
        "/api/integration/resources/document", params={"file_name": "missing.pdf"}
    ).status_code == 404


def test_catalog_excludes_unapproved_and_manifest_unlisted_sections():
    chunks = [
        {
            "chunk_id": "approved::chunk-001",
            "text": "Approved text.",
            "metadata": _metadata(section_id="approved"),
        },
        {
            "chunk_id": "rejected::chunk-001",
            "text": "Rejected draft must stay hidden.",
            "metadata": _metadata(section_id="rejected", section_classification="REVIEW_REQUIRED"),
        },
        {
            "chunk_id": "unlisted::chunk-001",
            "text": "Not in the active manifest.",
            "metadata": _metadata(section_id="unlisted"),
        },
    ]
    catalog = ResourceCatalog(chunks, approved_section_ids={"approved"})
    assert catalog.document_list()["counts"] == {
        "documents": 1, "approved_sections": 1, "indexed_chunks": 1,
    }
    assert catalog.search("Rejected draft") == []
    assert catalog.search("active manifest") == []
