"""Background tasks for MCP integration.

These are lightweight scaffolds. Replace with Celery tasks or worker processes
for production usage.
"""
import logging
from typing import Dict, Any
import requests
import os

logger = logging.getLogger(__name__)


def enqueue_download_and_ingest(payload: Dict[str, Any]):
    """Simple task to download file from MCP or provided URL and hand off to ingestion.

    This function runs in FastAPI BackgroundTasks context. For production, implement
    this as a persistent worker (Celery/RQ) with retries.
    """
    try:
        file_id = payload.get("file_id")
        download_url = payload.get("download_url")
        logger.info(f"[MCP TASK] Starting download for file_id={file_id}")

        if not download_url:
            logger.warning("No download_url provided in payload; skipping download")
            # TODO: implement MCP API call to fetch file bytes
            return

        # Download file (streaming for large files)
        resp = requests.get(download_url, stream=True, timeout=60)
        resp.raise_for_status()

        # Save to local temp path (developer convenience)
        storage_dir = os.getenv("LOCAL_CONTRACT_STORAGE", "/tmp/contracts")
        os.makedirs(storage_dir, exist_ok=True)

        filename = payload.get("name") or f"{file_id}"
        local_path = os.path.join(storage_dir, filename)

        with open(local_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        logger.info(f"[MCP TASK] Downloaded file to {local_path}")

        # TODO: call ingestion pipeline, parsing, DB insertion
        logger.info(f"[MCP TASK] TODO: enqueue parsing/ingestion for {local_path}")

    except Exception as e:
        logger.error(f"[MCP TASK] Failed to download/ingest: {str(e)}")
        # In production, record failure in DB and schedule retry
