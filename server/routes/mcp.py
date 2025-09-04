from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, status
from typing import Dict, Any
import logging

from utils.mcp_utils import verify_mcp_signature, MCPWebhookPayload
from tasks.mcp_tasks import enqueue_download_and_ingest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gdrive", tags=["MCP Integration"])


@router.post("/webhook")
async def mcp_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Endpoint to receive webhook notifications from the gdrive-mcp-server.
    Expected behavior:
      - verify signature
      - parse payload
      - enqueue background task to download and ingest file
    """
    try:
        body = await request.body()
        headers = request.headers

        # Verify signature (raises HTTPException if invalid)
        try:
            payload = verify_mcp_signature(body, headers)
        except Exception as e:
            logger.warning(f"Invalid MCP signature: {str(e)}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

        # Convert to payload dataclass for type safety
        mcp_payload = MCPWebhookPayload.parse_raw(body)

        logger.info(f"Received MCP webhook for file: {mcp_payload.file_id} name={mcp_payload.name}")

        # Enqueue background job (non-blocking)
        background_tasks.add_task(enqueue_download_and_ingest, mcp_payload.dict())

        return {"status": "accepted", "message": "Webhook received"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to handle MCP webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
