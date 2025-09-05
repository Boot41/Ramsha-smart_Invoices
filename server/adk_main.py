"""
Google ADK Main Entry Point

This is the main entry point for running the Smart Invoice Scheduler with Google ADK support.
"""

import os
import logging
from typing import Dict, Any

# Configure environment for Google ADK
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"

# Import after environment setup
from adk_agents.orchestrator_adk_workflow import create_adk_workflow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def main():
    """
    Main function for running ADK workflows
    """
    logger.info("🚀 Starting Smart Invoice Scheduler with Google ADK")
    
    # Verify environment variables
    required_env_vars = [
        "GOOGLE_API_KEY",
        "GOOGLE_CLOUD_PROJECT", 
        "GOOGLE_CLOUD_LOCATION"
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {missing_vars}")
        logger.info("Please set the following environment variables:")
        logger.info("  export GOOGLE_API_KEY=your_api_key_here")
        logger.info("  export GOOGLE_CLOUD_PROJECT=your_project_id")
        logger.info("  export GOOGLE_CLOUD_LOCATION=us-central1")
        return
    
    logger.info("✅ Environment variables configured")
    logger.info(f"   Project: {os.getenv('GOOGLE_CLOUD_PROJECT')}")
    logger.info(f"   Location: {os.getenv('GOOGLE_CLOUD_LOCATION')}")
    
    # Create ADK workflow
    try:
        workflow = create_adk_workflow()
        logger.info("✅ ADK workflow created successfully")
        
        # Test workflow creation
        logger.info("🧪 Testing ADK workflow...")
        
        test_result = await workflow.execute_workflow(
            user_id="test_user",
            contract_file="This is a test contract for ADK integration",
            contract_name="Test Contract",
            max_attempts=1,
            options={"test_mode": True}
        )
        
        logger.info(f"✅ Test workflow completed - Status: {test_result.get('processing_status')}")
        logger.info(f"   Workflow ID: {test_result.get('workflow_id')}")
        logger.info(f"   Events: {len(test_result.get('adk_events', []))}")
        
        # Print workflow summary
        logger.info("\n" + "="*50)
        logger.info("🎉 Google ADK Integration Successfully Configured!")
        logger.info("="*50)
        logger.info("Your Smart Invoice Scheduler now supports:")
        logger.info("  ✅ Google ADK multi-agent orchestration")
        logger.info("  ✅ Native Vertex AI integration")
        logger.info("  ✅ Event-driven workflow execution")
        logger.info("  ✅ Built-in error handling and retries")
        logger.info("  ✅ Real-time progress tracking")
        logger.info("  ✅ Human-in-the-loop validation")
        logger.info("="*50)
        
    except Exception as e:
        logger.error(f"❌ Failed to create ADK workflow: {str(e)}")
        logger.info("\nTroubleshooting:")
        logger.info("1. Ensure google-adk is installed: pip install google-adk")
        logger.info("2. Verify your Google Cloud credentials are configured")
        logger.info("3. Check that Vertex AI API is enabled in your project")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())