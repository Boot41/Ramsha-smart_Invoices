import os
import json
import vertexai
from fastapi import FastAPI
from datetime import datetime, date
from dotenv import load_dotenv, find_dotenv

from db.postgresdb import get_db
from utils.config import get_random_region

# Load environment variables from .env file
load_dotenv(find_dotenv())

# Setup logging before importing other modules
from utils.logging_config import setup_logging
setup_logging(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    log_file="smart_invoice_scheduler.log"
)

import logging
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from routes.routes import routes_router

# Get logger for main module
logger = logging.getLogger(__name__)

# Custom JSON encoder to handle date/datetime objects
def custom_json_serializer(obj):
    """Custom JSON serializer for date/datetime objects"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, date):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

class CustomJSONResponse(JSONResponse):
    """Custom JSON response that handles date/datetime serialization"""
    def render(self, content) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
            default=custom_json_serializer
        ).encode("utf-8")

app = FastAPI(default_response_class=CustomJSONResponse)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"]
)

app.include_router(routes_router)

@app.on_event("startup")
async def startup():
    logger.info("🚀 Smart Invoice Scheduler - Application Startup")
    logger.info(f"📅 Application starting up at {datetime.now()}")
    
    # Verify environment variables are loaded
    project_id = os.getenv("PROJECT_ID")
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    storage_bucket = os.getenv("GCP_STORAGE_BUCKET")
    get_db()

    vertexai.init(project=project_id, location=get_random_region())
    
    if project_id:
        logger.info(f"✅ PROJECT_ID loaded: {project_id}")
    else:
        logger.error("❌ PROJECT_ID not found in environment variables")
    
    if credentials_path:
        logger.info(f"✅ GOOGLE_APPLICATION_CREDENTIALS loaded: {credentials_path}")
        # Check if credentials file exists
        if os.path.exists(credentials_path):
            logger.info(f"✅ Credentials file exists at: {credentials_path}")
        else:
            logger.error(f"❌ Credentials file not found at: {credentials_path}")
    else:
        logger.error("❌ GOOGLE_APPLICATION_CREDENTIALS not found in environment variables")
    
    # Log storage bucket configuration
    if storage_bucket:
        logger.info(f"🪣 GCP Storage Bucket: {storage_bucket}")
    else:
        logger.info(f"🪣 GCP Storage Bucket: {project_id}-documents (default)")
    
    # Test services initialization
    try:
        from services.gcp_storage_service import get_gcp_storage_service
        storage_service = get_gcp_storage_service()
        logger.info("✅ GCP Storage Service initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize GCP Storage Service: {str(e)}")
    
    try:
        from models.llm.embedding import get_embedding_service
        embedding_service = get_embedding_service()
        logger.info("✅ LLM Embedding Service initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize LLM Embedding Service: {str(e)}")
    
    logger.info("🎯 Application startup completed - Ready to serve requests!")


@app.on_event("shutdown")
async def shutdown():
    logger.info("🛑 Smart Invoice Scheduler - Application Shutdown")
    logger.info("👋 Application shutdown completed")

@app.get("/health")
async def health_check():
    return {"status": "ok"}