# 🔄 Separated Workflow Implementation

## Overview

The MCP integration has been updated to implement a **separated workflow approach** where contract syncing and processing are distinct operations. This provides better control and prevents unnecessary processing overhead.

## Changes Made

### 🔧 Backend Changes

#### 1. **MCP Route Updates** (`server/routes/mcp.py`)
- **Default `process_files = false`**: Sync operations no longer process contracts by default
- **New response fields**: Added `sync_only` and `processing_note` to responses
- **Clear separation**: Users must explicitly request processing during sync

#### 2. **API Documentation Updates** (`server/API_DOCUMENTATION.md`)
- **Separated workflow section**: Explains the two-phase approach
- **Updated examples**: Shows sync-only and optional processing workflows
- **Response documentation**: Documents both sync-only and processing responses

### 💻 Frontend Changes

#### 1. **API Layer Updates** (`client/api/contracts.ts`)
- **Optional userId**: Sync methods no longer require userId for sync-only operations
- **Updated interfaces**: Added `sync_only` and `processing_note` fields
- **Default `processFiles = false`**: Sync operations default to sync-only mode

#### 2. **Contract Store Updates** (`client/stores/contractStore.ts`)
- **Method signatures**: Updated to reflect optional userId and default processFiles=false
- **Return types**: Methods now return response objects for better error handling

#### 3. **Example Component** (`client/examples/SeparatedWorkflowExample.tsx`)
- **Complete workflow demo**: Shows how to implement the separated approach
- **UI patterns**: Demonstrates sync → select → process flow

## Workflow Phases

### Phase 1: 📥 Sync Contracts
```bash
# Sync all contracts (no processing)
GET /api/v1/mcp/gdrive/contracts

# Sync rental contracts only
GET /api/v1/mcp/gdrive/rental-contracts
```

**Benefits:**
- Fast retrieval of available contracts
- No processing overhead
- Browse before processing
- Cost-effective for large contract libraries

### Phase 2: 🚀 Process Selected Contracts
```bash
# Start agentic workflow for specific contracts
POST /api/v1/orchestrator/workflow/invoice/start
```

**Benefits:**
- User selects specific contracts to process
- Full agentic workflow with AI agents
- Generates invoices only when needed
- Better resource management

## API Response Examples

### Sync-Only Response (Default)
```json
{
  "status": "success",
  "message": "Successfully synced 3 contract files from Google Drive",
  "contracts": [
    {
      "file_id": "1ABC123...",
      "name": "Service Agreement.pdf",
      "mime_type": "application/pdf",
      "gdrive_uri": "gdrive:///1ABC123..."
    }
  ],
  "total_count": 3,
  "processed_count": 0,
  "sync_only": true,
  "processing_note": "Contracts are synced only. Use POST /api/v1/orchestrator/workflow/invoice/start to process contracts and generate invoices."
}
```

### Optional Processing Response
```json
{
  "status": "success",
  "total_count": 3,
  "processed_count": 2,
  "sync_only": false,
  "processing_note": null
}
```

## Frontend Usage Examples

### Simple Sync
```typescript
import { useContractStore } from '../stores/contractStore';

const { syncMCPContracts } = useContractStore();

// Sync only - no processing
await syncMCPContracts();

// Sync with processing (optional)
await syncMCPContracts('user123', undefined, true);
```

### Rental Contracts
```typescript
const { syncMCPRentalContracts } = useContractStore();

// Sync rental contracts only
await syncMCPRentalContracts();
```

### Complete Workflow
```typescript
// Phase 1: Sync
const response = await syncMCPContracts();
console.log(`Found ${response.total_count} contracts`);

// Phase 2: Process selected contracts
for (const contract of selectedContracts) {
  await startInvoiceWorkflow(file, userId, contract.name);
}
```

## Migration Guide

### For Existing Code

#### Before (Automatic Processing)
```typescript
// Old approach - always processed
await syncMCPContracts('user123', 'contract', true);
```

#### After (Separated Workflow)
```typescript
// New approach - sync first
const response = await syncMCPContracts();

// Then process selected contracts
if (userWantsToProcess) {
  await syncMCPContracts('user123', 'contract', true);
  // OR use agentic workflow endpoint
}
```

### Benefits of Migration

1. **🚀 Performance**: Faster sync operations
2. **💰 Cost Control**: Process only what you need
3. **🎯 Selective Processing**: Choose specific contracts
4. **📊 Better UX**: Users see available contracts before processing
5. **🔧 Resource Management**: Avoid unnecessary API calls and processing

## Configuration

### Environment Variables
No new environment variables required. Existing MCP configuration works as-is.

### Default Behavior
- **Sync endpoints**: Default to `process_files=false`
- **Frontend methods**: Default to sync-only mode
- **Backwards compatibility**: Can still enable processing with `process_files=true`

## Testing

### Backend
```bash
# Test sync-only
curl -X GET "http://localhost:8000/api/v1/mcp/gdrive/contracts"

# Test with processing
curl -X GET "http://localhost:8000/api/v1/mcp/gdrive/contracts?user_id=user123&process_files=true"
```

### Frontend
```typescript
// Test in your React components
const response = await syncMCPContracts();
console.log('Sync only:', response.sync_only); // Should be true
```

This separated workflow approach provides better control, performance, and user experience while maintaining full backwards compatibility with existing processing capabilities.