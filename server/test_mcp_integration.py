#!/usr/bin/env python3
"""
Test script for MCP Integration with Google Drive

This script demonstrates and tests the MCP (Model Context Protocol) integration
for syncing contract files from Google Drive.

Usage:
    python test_mcp_integration.py

Requirements:
    - MCP Google Drive server built and available
    - Google Drive credentials configured
    - MCP_SHARED_SECRET environment variable set
"""

import asyncio
import os
import sys
sys.path.append(os.path.dirname(__file__))

from services.mcp_service import get_mcp_service
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_mcp_service():
    """Test the MCP service functionality"""
    try:
        logger.info("🚀 Testing MCP Service Integration")
        
        # Initialize MCP service
        mcp_service = get_mcp_service()
        logger.info("✅ MCP Service initialized successfully")
        
        # Test 1: Search for contract files
        logger.info("🔍 Test 1: Searching for contract files...")
        contracts = mcp_service.search_contracts("contract OR agreement")
        logger.info(f"✅ Found {len(contracts)} contract files")
        
        if contracts:
            logger.info("📄 Contract files found:")
            for i, contract in enumerate(contracts[:3]):  # Show first 3
                logger.info(f"  {i+1}. {contract['name']} ({contract['mime_type']})")
        
        # Test 2: Test file reading (if contracts found)
        if contracts:
            test_contract = contracts[0]
            logger.info(f"📖 Test 2: Reading content from '{test_contract['name']}'...")
            
            try:
                content, mime_type = mcp_service.read_file_content(test_contract['file_id'])
                content_preview = content[:200] + "..." if len(content) > 200 else content
                logger.info(f"✅ Successfully read file content (first 200 chars): {content_preview}")
            except Exception as e:
                logger.warning(f"⚠️  Could not read file content: {e}")
        
        logger.info("🎉 MCP Service tests completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ MCP Service test failed: {e}")
        return False


def test_mcp_server_availability():
    """Test if MCP server is available and built"""
    try:
        logger.info("🔧 Testing MCP Server Availability...")
        
        # Check if MCP server exists
        base_path = os.path.dirname(os.path.dirname(__file__))
        mcp_path = os.path.join(
            base_path, "mcp", "gdrive_mcp", "gdrive-mcp-server", "dist", "index.js"
        )
        
        if os.path.exists(mcp_path):
            logger.info(f"✅ MCP Server found at: {mcp_path}")
            return True
        else:
            logger.error(f"❌ MCP Server not found at: {mcp_path}")
            logger.info("💡 Make sure to build the MCP server with: cd mcp/gdrive_mcp/gdrive-mcp-server && npm run build")
            return False
    
    except Exception as e:
        logger.error(f"❌ Failed to check MCP server: {e}")
        return False


def test_environment_setup():
    """Test environment configuration"""
    logger.info("🔐 Testing Environment Configuration...")
    
    issues = []
    
    # Check MCP shared secret
    if not os.getenv("MCP_SHARED_SECRET"):
        issues.append("MCP_SHARED_SECRET environment variable not set")
    else:
        logger.info("✅ MCP_SHARED_SECRET is configured")
    
    # Check Google credentials
    google_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not google_creds:
        issues.append("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
    elif not os.path.exists(google_creds):
        issues.append(f"Google credentials file not found: {google_creds}")
    else:
        logger.info("✅ Google credentials are configured")
    
    if issues:
        logger.warning("⚠️  Environment issues found:")
        for issue in issues:
            logger.warning(f"  - {issue}")
        return False
    else:
        logger.info("✅ Environment configuration looks good")
        return True


async def main():
    """Main test function"""
    logger.info("🎯 Starting MCP Integration Tests")
    logger.info("=" * 50)
    
    # Test 1: Environment setup
    env_ok = test_environment_setup()
    
    # Test 2: MCP server availability
    server_ok = test_mcp_server_availability()
    
    # Test 3: MCP service functionality (only if server is available)
    service_ok = False
    if server_ok:
        service_ok = await test_mcp_service()
    else:
        logger.warning("⏭️  Skipping MCP service tests (server not available)")
    
    # Summary
    logger.info("=" * 50)
    logger.info("📊 Test Results Summary:")
    logger.info(f"  Environment Setup: {'✅ PASS' if env_ok else '❌ FAIL'}")
    logger.info(f"  MCP Server: {'✅ PASS' if server_ok else '❌ FAIL'}")
    logger.info(f"  MCP Service: {'✅ PASS' if service_ok else '⏭️  SKIPPED' if not server_ok else '❌ FAIL'}")
    
    if all([env_ok, server_ok, service_ok]):
        logger.info("🎉 All tests passed! MCP integration is ready.")
        return 0
    else:
        logger.info("⚠️  Some tests failed. Check the logs above for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)