"""Read-only API for browsing approved document and section metadata."""

from __future__ import annotations

from functools import lru_cache
import json

from fastapi import APIRouter, HTTPException, Query

from brain.config import load_config
from brain.vector_store import get_vector_store
from integration.resource_catalog import ResourceCatalog


router = APIRouter(prefix="/api/integration/resources", tags=["resources"])


@lru_cache(maxsize=1)
def get_resource_catalog() -> ResourceCatalog:
    config = load_config()
    store = get_vector_store(config)
    with config.prototype_manifest_path.open(encoding="utf-8") as manifest_file:
        manifest = json.load(manifest_file)
    approved_section_ids = {
        str(section.get("section_id"))
        for section in manifest.get("sections", [])
        if section.get("section_id")
    }
    return ResourceCatalog(
        store.chunks,
        overlap_chars=config.chunk_overlap_chars,
        approved_section_ids=approved_section_ids,
    )


@router.get("")
def list_resources():
    """List approved documents and live counts without returning chunk internals."""
    return get_resource_catalog().document_list()


@router.get("/search")
def search_resources(
    q: str = Query(..., min_length=1, max_length=200),
    limit: int = Query(20, ge=1, le=50),
):
    return {"query": q, "results": get_resource_catalog().search(q, limit=limit)}


@router.get("/document")
def get_resource_document(file_name: str = Query(..., min_length=1, max_length=240)):
    document = get_resource_catalog().get_document(file_name)
    if document is None:
        raise HTTPException(status_code=404, detail="Approved document not found.")
    return document
