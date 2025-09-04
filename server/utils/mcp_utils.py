"""Utility helpers for MCP (gdrive-mcp) integration.

Includes signature verification helper and a small Pydantic model for webhook payloads.
"""
from typing import Dict, Any
import os
import hmac
import hashlib
import json
import logging

from pydantic import BaseModel
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class MCPWebhookPayload(BaseModel):
    file_id: str
    name: str
    mime_type: str | None = None
    size: int | None = None
    drive_id: str | None = None
    download_url: str | None = None
    modified_time: str | None = None


def verify_mcp_signature(body: bytes, headers: Dict[str, str]) -> MCPWebhookPayload:
    """
    Verify HMAC signature included by MCP server.

    Expects header `X-MCP-Signature` with HMAC-SHA256 hex digest of body using secret
    from env var `MCP_SHARED_SECRET`.

    Returns parsed MCPWebhookPayload or raises HTTPException.
    """
    secret = os.getenv("MCP_SHARED_SECRET")
    if not secret:
        logger.error("MCP_SHARED_SECRET not configured in environment")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="MCP secret not configured")

    signature_header = headers.get("x-mcp-signature") or headers.get("X-MCP-Signature")
    if not signature_header:
        logger.warning("Missing MCP signature header")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing signature")

    computed = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed, signature_header):
        logger.warning("MCP signature mismatch")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    # Parse payload
    try:
        payload_json = json.loads(body.decode())
        payload = MCPWebhookPayload(**payload_json)
        return payload
    except Exception as e:
        logger.error(f"Failed to parse MCP payload: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payload")
