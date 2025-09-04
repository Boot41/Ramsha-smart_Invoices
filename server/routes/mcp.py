from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, status, Depends, Query
from typing import Dict, Any, Optional
import logging
import os

from utils.mcp_utils import verify_mcp_signature
from tasks.mcp_tasks import enqueue_download_and_ingest
from services.contract_processor import get_contract_processor
from services.mcp_service import get_mcp_service
from middleware.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gdrive", tags=["MCP Integration"])


@router.get("/contracts")
async def sync_contracts_from_drive(
    query: Optional[str] = Query(default="contract", description="Search query for contract files"),
    process_files: bool = Query(default=False, description="Whether to automatically process found contracts"),
    user_id: Optional[str] = Query(default=None, description="User ID for contract processing"),
    _current_user = Depends(get_current_user)  # Prefix with underscore to indicate it's not used
):
    """
    Sync and retrieve contract files from Google Drive using MCP server.
    
    This endpoint demonstrates the key benefits of using MCP over direct API calls:
    1. Standardized protocol for AI/LLM systems to interact with external tools
    2. Consistent authentication and authorization handling
    3. Built-in error handling and retry mechanisms
    4. Clean abstraction layer between your application and Google Drive API
    5. Extensible to other file storage systems with same interface
    """
    try:
        logger.info(f"🔍 Searching Google Drive for contracts with query: {query}")
        
        # Use MCP service for clean abstraction
        mcp_service = get_mcp_service()
        
        # Search for contract files
        contracts_found = mcp_service.search_contracts(query)
        
        if not contracts_found:
            return {
                "status": "success",
                "message": "No contract files found in Google Drive",
                "contracts": [],
                "total_count": 0,
                "sync_only": True,
                "processing_note": "Contracts are synced only. Use the agentic workflow endpoints to process and generate invoices."
            }
        
        logger.info(f"✅ Found {len(contracts_found)} contract files in Google Drive")
        
        # Process files if requested
        processed_contracts = []
        if process_files and contracts_found and user_id:
            logger.info(f"🔄 Processing {len(contracts_found)} contracts...")
            
            contract_processor = get_contract_processor()
            
            for contract in contracts_found:
                try:
                    # Download file to temporary location
                    tmp_file_path = mcp_service.download_file_to_temp(
                        contract["file_id"], 
                        contract["name"]
                    )
                    
                    # Process the contract
                    with open(tmp_file_path, 'rb') as f:
                        processing_result = await contract_processor.process_contract(
                            pdf_file=f.read(),
                            user_id=user_id,
                            contract_name=contract["name"]
                        )
                    
                    # Clean up temporary file
                    os.unlink(tmp_file_path)
                    
                    processed_contracts.append({
                        **contract,
                        "processing_result": processing_result,
                        "processed": True
                    })
                    
                    logger.info(f"✅ Processed contract: {contract['name']}")
                
                except Exception as e:
                    logger.error(f"❌ Failed to process contract {contract['name']}: {str(e)}")
                    processed_contracts.append({
                        **contract,
                        "processing_error": str(e),
                        "processed": False
                    })
        
        result = {
            "status": "success",
            "message": f"Successfully synced {len(contracts_found)} contract files from Google Drive",
            "contracts": processed_contracts if process_files and user_id else contracts_found,
            "total_count": len(contracts_found),
            "processed_count": len([c for c in processed_contracts if c.get("processed", False)]) if process_files else 0,
            "sync_only": not (process_files and user_id),
            "processing_note": "Contracts are synced only. Use POST /api/v1/orchestrator/workflow/invoice/start to process contracts and generate invoices." if not (process_files and user_id) else None,
            "mcp_benefits_used": [
                "Standardized file search across cloud storage",
                "Consistent authentication handling", 
                "Built-in error handling and retries",
                "Clean abstraction from Google Drive API complexity",
                "Extensible to other storage providers with same interface"
            ]
        }
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Failed to sync contracts from Google Drive: {str(e)}")
        
        # Import the custom OAuth error
        from services.mcp_service import OAuthExpiredError
        
        # Check for OAuth token expiration errors
        if isinstance(e, OAuthExpiredError):
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "oauth_expired",
                    "message": "Google Drive authentication has expired. Please re-authenticate.",
                    "requires_auth": True,
                    "auth_url": "/auth/google-drive"
                }
            )
        
        # Also check error message for backward compatibility
        error_msg = str(e).lower()
        if "invalid_request" in error_msg or "unauthorized" in error_msg or "token" in error_msg:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "oauth_expired",
                    "message": "Google Drive authentication has expired. Please re-authenticate.",
                    "requires_auth": True,
                    "auth_url": "/auth/google-drive"
                }
            )
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync contracts: {str(e)}"
        )


@router.get("/rental-contracts")
async def sync_rental_contracts_from_drive(
    query: Optional[str] = Query(default="rental", description="Search query for rental contract files"),
    process_files: bool = Query(default=False, description="Whether to automatically process found rental contracts"),
    user_id: Optional[str] = Query(default=None, description="User ID for contract processing"),
    _current_user = Depends(get_current_user)
):
    """
    Sync and retrieve specifically rental contract files from Google Drive using MCP server.
    
    This endpoint is optimized for finding rental agreements, lease contracts, and property-related documents.
    """
    try:
        logger.info(f"🏠 Searching Google Drive for rental contracts with query: {query}")
        
        # Use MCP service for rental-specific search
        mcp_service = get_mcp_service()
        
        # Search for rental contract files using the specialized method
        rental_contracts_found = mcp_service.search_rental_contracts(query)
        
        if not rental_contracts_found:
            return {
                "status": "success",
                "message": "No rental contract files found in Google Drive",
                "contracts": [],
                "total_count": 0,
                "sync_only": True,
                "processing_note": "Contracts are synced only. Use the agentic workflow endpoints to process and generate invoices."
            }
        
        logger.info(f"✅ Found {len(rental_contracts_found)} rental contract files in Google Drive")
        
        # Process files if requested
        processed_contracts = []
        if process_files and rental_contracts_found and user_id:
            logger.info(f"🔄 Processing {len(rental_contracts_found)} rental contracts...")
            
            contract_processor = get_contract_processor()
            
            for contract in rental_contracts_found:
                try:
                    # Download file to temporary location
                    tmp_file_path = mcp_service.download_file_to_temp(
                        contract["file_id"], 
                        contract["name"]
                    )
                    
                    # Process the rental contract
                    with open(tmp_file_path, 'rb') as f:
                        processing_result = await contract_processor.process_contract(
                            pdf_file=f.read(),
                            user_id=user_id,
                            contract_name=contract["name"]
                        )
                    
                    # Clean up temporary file
                    os.unlink(tmp_file_path)
                    
                    processed_contracts.append({
                        **contract,
                        "processing_result": processing_result,
                        "processed": True,
                        "contract_type": "rental_lease"  # Mark as rental contract
                    })
                    
                    logger.info(f"✅ Processed rental contract: {contract['name']}")
                
                except Exception as e:
                    logger.error(f"❌ Failed to process rental contract {contract['name']}: {str(e)}")
                    processed_contracts.append({
                        **contract,
                        "processing_error": str(e),
                        "processed": False,
                        "contract_type": "rental_lease"
                    })
        
        result = {
            "status": "success",
            "message": f"Successfully synced {len(rental_contracts_found)} rental contract files from Google Drive",
            "contracts": processed_contracts if process_files and user_id else rental_contracts_found,
            "total_count": len(rental_contracts_found),
            "processed_count": len([c for c in processed_contracts if c.get("processed", False)]) if process_files else 0,
            "sync_only": not (process_files and user_id),
            "processing_note": "Contracts are synced only. Use POST /api/v1/orchestrator/workflow/invoice/start to process contracts and generate invoices." if not (process_files and user_id) else None,
            "contract_type_focus": "rental_lease",
            "rental_specific_features": [
                "Enhanced filtering for rental/lease keywords",
                "Optimized search for property-related documents",
                "Automatic contract_type classification as rental_lease"
            ]
        }
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Failed to sync rental contracts from Google Drive: {str(e)}")
        
        # Import the custom OAuth error
        from services.mcp_service import OAuthExpiredError
        
        # Check for OAuth token expiration errors
        if isinstance(e, OAuthExpiredError):
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "oauth_expired",
                    "message": "Google Drive authentication has expired. Please re-authenticate.",
                    "requires_auth": True,
                    "auth_url": "/auth/google-drive"
                }
            )
        
        # Also check error message for backward compatibility
        error_msg = str(e).lower()
        if "invalid_request" in error_msg or "unauthorized" in error_msg or "token" in error_msg:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "oauth_expired",
                    "message": "Google Drive authentication has expired. Please re-authenticate.",
                    "requires_auth": True,
                    "auth_url": "/auth/google-drive"
                }
            )
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync rental contracts: {str(e)}"
        )


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

        # Verify signature and parse payload
        try:
            mcp_payload = verify_mcp_signature(body, headers)
        except Exception as e:
            logger.warning(f"Invalid MCP signature: {str(e)}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

        logger.info(f"Received MCP webhook for file: {mcp_payload.file_id} name={mcp_payload.name}")

        # Enqueue background job (non-blocking)
        background_tasks.add_task(enqueue_download_and_ingest, mcp_payload.model_dump())

        return {"status": "accepted", "message": "Webhook received"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to handle MCP webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
