# MCP (Model Context Protocol) Integration Guide

## Overview

This document explains the MCP integration in the Smart Invoice Scheduler, specifically for syncing contract files from Google Drive.

## What is MCP and Why Use It?

**Model Context Protocol (MCP)** is a standardized protocol designed for AI/LLM systems to interact with external tools and resources. Instead of using direct API calls to Google Drive, we use MCP for several key benefits:

### Benefits of MCP over Direct API Calls:

1. **Standardization**: Provides a consistent interface across different external services
2. **Authentication Management**: Handles OAuth and credential management automatically
3. **Error Handling**: Built-in retry mechanisms and error handling
4. **AI-Optimized**: Designed specifically for LLM/AI system interactions
5. **Extensibility**: Easy to swap or add new storage providers with the same interface
6. **Security**: Standardized signature verification for webhooks

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   MCP Service   │    │  Google Drive   │
│   Server        │◄──►│   (gdrive-mcp)  │◄──►│   API           │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│  Contract       │    │  File Content   │
│  Processing     │    │  Retrieval      │
└─────────────────┘    └─────────────────┘
```

## Components

### 1. MCP Server (`/mcp/gdrive_mcp/`)
- TypeScript-based Google Drive MCP server
- Handles authentication with Google Drive
- Provides standardized tools: `gdrive_search` and `gdrive_read_file`

### 2. MCP Service (`/server/services/mcp_service.py`)
- Python service that communicates with the MCP server
- Abstracts MCP protocol details from the main application
- Provides clean Python interface for file operations

### 3. MCP Routes (`/server/routes/mcp.py`)
- FastAPI endpoints for contract synchronization
- Webhook handler for real-time file change notifications
- Integration with contract processing pipeline

### 4. Webhook Utils (`/server/utils/mcp_utils.py`)
- HMAC signature verification for webhook security
- Pydantic models for type-safe webhook payloads

## API Endpoints

### GET `/api/v1/mcp/gdrive/contracts`

Sync and retrieve contract files from Google Drive.

**Parameters:**
- `query` (optional): Search query for contract files (default: "contract OR agreement")
- `process_files` (boolean): Whether to automatically process found contracts (default: true)
- `user_id` (optional): User ID for contract processing

**Response:**
```json
{
  "status": "success",
  "message": "Successfully synced 3 contract files from Google Drive",
  "contracts": [
    {
      "file_id": "1ABC123...",
      "name": "Service Agreement.pdf",
      "mime_type": "application/pdf",
      "gdrive_uri": "gdrive:///1ABC123...",
      "processing_result": {
        "status": "success",
        "contract_id": "cont_456...",
        "chunks_created": 15,
        "embeddings_generated": 15
      },
      "processed": true
    }
  ],
  "total_count": 3,
  "processed_count": 2,
  "mcp_benefits_used": [
    "Standardized file search across cloud storage",
    "Consistent authentication handling",
    "Built-in error handling and retries",
    "Clean abstraction from Google Drive API complexity",
    "Extensible to other storage providers with same interface"
  ]
}
```

### POST `/api/v1/mcp/gdrive/webhook`

Receives webhook notifications when files change in Google Drive.

**Headers:**
- `X-MCP-Signature`: HMAC-SHA256 signature for verification

**Payload:**
```json
{
  "file_id": "1ABC123...",
  "name": "Updated Contract.pdf",
  "mime_type": "application/pdf",
  "size": 1024000,
  "modified_time": "2023-12-01T10:00:00Z"
}
```

## Setup Instructions

### 1. Configure MCP Server

```bash
cd mcp/gdrive_mcp/gdrive-mcp-server
npm install
npm run build

# Authenticate with Google Drive
node dist/index.js auth
```

### 2. Set Environment Variables

```bash
# Required for webhook signature verification
export MCP_SHARED_SECRET="your-secret-key"

# Google Drive API credentials
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"

# Optional: Local storage for downloaded contracts
export LOCAL_CONTRACT_STORAGE="/tmp/contracts"
```

### 3. Test the Integration

```bash
cd server
python test_mcp_integration.py
```

## Usage Examples

### Basic Contract Sync

```python
import requests

# Sync all contract files
response = requests.get(
    "http://localhost:8000/api/v1/mcp/gdrive/contracts",
    headers={"Authorization": "Bearer your-token"},
    params={
        "user_id": "user123",
        "process_files": True
    }
)

contracts = response.json()["contracts"]
print(f"Found {len(contracts)} contracts")
```

### Search with Custom Query

```python
# Search for specific types of contracts
response = requests.get(
    "http://localhost:8000/api/v1/mcp/gdrive/contracts",
    headers={"Authorization": "Bearer your-token"},
    params={
        "query": "consulting agreement 2024",
        "user_id": "user123"
    }
)
```

### List Only (No Processing)

```python
# Just list files without processing
response = requests.get(
    "http://localhost:8000/api/v1/mcp/gdrive/contracts",
    headers={"Authorization": "Bearer your-token"},
    params={
        "process_files": False
    }
)
```

## Error Handling

The MCP integration includes comprehensive error handling:

1. **Connection Errors**: Automatic retries for transient failures
2. **Authentication Errors**: Clear error messages for credential issues
3. **File Processing Errors**: Individual file failures don't stop the batch
4. **Timeout Protection**: Commands have configurable timeouts

## Security Considerations

1. **Webhook Security**: HMAC-SHA256 signature verification prevents unauthorized webhooks
2. **Authentication**: Google OAuth2 handled securely by MCP server
3. **Temporary Files**: Downloaded files are automatically cleaned up
4. **Access Control**: All endpoints require valid authentication tokens

## Monitoring and Logging

The integration provides detailed logging for:
- File search operations
- Download progress
- Processing results
- Error conditions
- Performance metrics

## Extending to Other Storage Providers

The MCP architecture makes it easy to add other storage providers:

1. **Implement MCP Server**: Create a new MCP server for the provider
2. **Update MCP Service**: Add provider-specific methods
3. **Add Routes**: Create new endpoints or extend existing ones
4. **Configure**: Add environment variables and authentication

Example providers that could be added:
- Dropbox MCP Server
- OneDrive MCP Server
- Amazon S3 MCP Server
- Local File System MCP Server

## Troubleshooting

### Common Issues

1. **MCP Server Not Found**
   - Ensure the MCP server is built: `npm run build`
   - Check the server path in `mcp_service.py`

2. **Authentication Errors**
   - Verify Google credentials are configured
   - Check if credentials file exists and is readable
   - Re-run authentication: `node dist/index.js auth`

3. **Webhook Signature Failures**
   - Verify `MCP_SHARED_SECRET` is set correctly
   - Check webhook payload format
   - Ensure signature header is included

4. **File Processing Errors**
   - Check contract processing service logs
   - Verify user permissions for contract processing
   - Ensure file formats are supported (PDF, DOC, etc.)

### Debug Mode

Enable debug logging by setting:
```bash
export LOG_LEVEL=DEBUG
```

This will show detailed MCP communication and processing steps.

## Performance Considerations

- **Batch Processing**: Multiple files are processed concurrently
- **Streaming**: Large files are downloaded in chunks to avoid memory issues
- **Caching**: Consider implementing caching for frequently accessed files
- **Rate Limiting**: Google Drive API has rate limits; MCP handles this automatically

## Future Enhancements

1. **Real-time Sync**: Implement webhook-based real-time synchronization
2. **Selective Sync**: Add filters for file types, dates, or folders
3. **Conflict Resolution**: Handle concurrent file modifications
4. **Delta Sync**: Only sync changed files to improve performance
5. **Multi-tenancy**: Support multiple Google Drive accounts per user