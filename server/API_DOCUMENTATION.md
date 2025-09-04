# Smart Invoice Scheduler - API Documentation

## Overview

The Smart Invoice Scheduler is an AI-powered system that automates contract processing and invoice generation using an agentic workflow architecture. This documentation covers all API endpoints and explains how the multi-agent system processes contracts into invoices.

## Base URL

```
http://localhost:8000
```

## Authentication

Most endpoints require JWT authentication. Include the token in the Authorization header:

```bash
Authorization: Bearer <your-jwt-token>
```

---

# 🤖 Agentic Workflow Overview

The system uses a **multi-agent architecture** where specialized AI agents collaborate to process contracts and generate invoices. Here's how the workflow operates:

## Workflow Architecture

```mermaid
graph TB
    A[Contract Upload] --> B[📋 Orchestrator Agent]
    B --> C[📄 Contract Processing Agent]
    C --> D[✅ Validation Agent]
    D --> E[🔧 Correction Agent]
    E --> F[💰 Invoice Generator Agent]
    F --> G[🎨 UI Invoice Generator Agent]
    G --> H[📅 Schedule Extraction]
    H --> I[🔍 Quality Assurance]
    I --> J[💾 Storage & Scheduling]
    J --> K[📊 Feedback Learning]
    K --> L[✅ Workflow Complete]
    
    D -->|Needs Human Input| M[👤 Human Input]
    M --> E
    
    style B fill:#e1f5fe
    style C fill:#f3e5f5
    style D fill:#e8f5e8
    style E fill:#fff3e0
    style F fill:#fce4ec
    style G fill:#e0f2f1
```

## Agent Responsibilities

### 🧠 **Orchestrator Agent**
- **Role**: Master coordinator that decides the next step in the workflow
- **Functions**: 
  - Routes workflow to appropriate agents
  - Handles error recovery and retry logic
  - Manages workflow state transitions
  - Prevents infinite loops with decision count limits

### 📄 **Contract Processing Agent**
- **Role**: Extracts and structures contract information
- **Functions**:
  - Parses contract PDFs using OCR and NLP
  - Extracts key information (parties, terms, amounts, dates)
  - Creates embeddings for RAG-based querying
  - Stores processed contract in vector database

### ✅ **Validation Agent**
- **Role**: Ensures data quality and completeness
- **Functions**:
  - Validates extracted contract information
  - Identifies missing or ambiguous data
  - Requests human input when needed
  - Checks data consistency and business rules

### 🔧 **Correction Agent**
- **Role**: Fixes issues and generates final invoice structure
- **Functions**:
  - Incorporates human feedback
  - Corrects validation errors
  - Generates structured invoice JSON
  - Applies business logic transformations

### 💰 **Invoice Generator Agent**
- **Role**: Creates invoice records in the database
- **Functions**:
  - Stores invoice data with proper relationships
  - Generates unique invoice IDs
  - Handles financial calculations
  - Creates audit trail entries

### 🎨 **UI Invoice Generator Agent**
- **Role**: Creates beautiful, professional invoice templates
- **Functions**:
  - Generates HTML/CSS invoice templates
  - Applies branding and styling
  - Creates responsive designs
  - Produces PDF-ready templates

## Workflow State Management

The workflow maintains a shared state object that passes between agents:

```json
{
  "workflow_id": "uuid-string",
  "user_id": "user123",
  "processing_status": "processing|success|failed|waiting_for_human_input",
  "attempt_count": 1,
  "orchestrator_decision_count": 3,
  "contract_data": {...},
  "validation_results": {...},
  "invoice_data": {...},
  "ui_template": "...",
  "schedule_data": {...},
  "errors": [...],
  "workflow_completed": false,
  "human_input_required": false,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:05:00Z"
}
```

---

# 📚 API Endpoints

## 🔐 Authentication Endpoints

### Register User
```http
POST /auth/register
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "secure_password",
  "full_name": "John Doe"
}
```

### Login
```http
POST /auth/login
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "access_token": "jwt-token",
  "token_type": "bearer",
  "user_id": "user123"
}
```

### Get User Profile
```http
GET /auth/profile
Authorization: Bearer <token>
```

### Update Profile
```http
PUT /auth/profile
Authorization: Bearer <token>
```

### Reset Password
```http
POST /auth/forgot-password
```

---

## 🤖 Agentic Orchestrator Endpoints

### Start Invoice Workflow
```http
POST /api/v1/orchestrator/workflow/invoice/start
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Form Data:**
- `user_id`: User identifier
- `contract_name`: Name of the contract
- `max_attempts`: Maximum retry attempts (default: 3)
- `options`: JSON string with additional options
- `contract_file`: PDF contract file

**Response:**
```json
{
  "workflow_id": "uuid-123",
  "status": "started",
  "message": "Agentic workflow initiated successfully",
  "expected_completion_time": "2024-01-01T00:10:00Z"
}
```

### Get Workflow Status
```http
GET /api/v1/orchestrator/workflow/{workflow_id}/status
Authorization: Bearer <token>
```

**Response:**
```json
{
  "workflow_id": "uuid-123",
  "status": "processing",
  "current_agent": "validation_agent",
  "progress_percentage": 60,
  "estimated_completion": "2024-01-01T00:05:00Z",
  "last_updated": "2024-01-01T00:03:00Z"
}
```

### Get Generated Invoice
```http
GET /api/v1/orchestrator/workflow/{workflow_id}/invoice
Authorization: Bearer <token>
```

**Response:**
```json
{
  "invoice_id": "inv-123",
  "workflow_id": "uuid-123",
  "invoice_data": {
    "invoice_number": "INV-2024-001",
    "amount": 5000.00,
    "currency": "USD",
    "due_date": "2024-01-31",
    "client_info": {...},
    "line_items": [...]
  },
  "pdf_url": "/invoices/inv-123.pdf"
}
```

### Get UI Template
```http
GET /api/v1/orchestrator/workflow/{workflow_id}/ui-template
Authorization: Bearer <token>
```

**Response:**
```json
{
  "template_html": "<html>...</html>",
  "template_css": "body { ... }",
  "preview_url": "/templates/preview/uuid-123"
}
```

### Cancel Workflow
```http
DELETE /api/v1/orchestrator/workflow/{workflow_id}/cancel
Authorization: Bearer <token>
```

### List Active Workflows
```http
GET /api/v1/orchestrator/workflows/active
Authorization: Bearer <token>
```

---

## 📄 Contract Processing Endpoints

### Upload and Process Contract
```http
POST /contracts/upload-and-process
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Form Data:**
- `file`: PDF contract file
- `user_id`: User identifier

**Response:**
```json
{
  "status": "success",
  "contract_id": "cont-123",
  "processing_result": {
    "chunks_created": 15,
    "embeddings_generated": 15,
    "text_preview": "This agreement is made between..."
  }
}
```

### Generate Invoice Data from Contract
```http
POST /contracts/generate-invoice-data
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "user_id": "user123",
  "contract_name": "service-agreement.pdf",
  "query": "Extract comprehensive invoice data"
}
```

### Query Contract
```http
POST /contracts/query
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "user_id": "user123",
  "contract_name": "service-agreement.pdf",
  "query": "What is the payment schedule?"
}
```

### Get User Contracts
```http
GET /contracts/user/{user_id}
Authorization: Bearer <token>
```

### Complete Contract-to-Invoice Workflow
```http
POST /contracts/process-and-generate-invoice
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

---

## 🔌 MCP (Google Drive) Integration Endpoints

**Important**: MCP endpoints now use a **separated workflow approach**:
1. **Sync Phase**: Retrieve and catalog contract files from Google Drive (no processing)
2. **Processing Phase**: Use agentic workflow endpoints to process contracts and generate invoices

This separation allows you to:
- Browse available contracts before processing
- Choose specific contracts for invoice generation
- Avoid unnecessary processing overhead during sync operations

### Sync Contracts from Google Drive
```http
GET /api/v1/mcp/gdrive/contracts
Authorization: Bearer <token>
```

**Query Parameters:**
- `query`: Search query for contract files (default: "contract")
- `process_files`: Whether to automatically process found contracts (default: false)
- `user_id`: User ID for contract processing (only required if process_files=true)

**Response (Sync Only - Default):**
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
  "processing_note": "Contracts are synced only. Use POST /api/v1/orchestrator/workflow/invoice/start to process contracts and generate invoices.",
  "mcp_benefits_used": [
    "Standardized file search across cloud storage",
    "Consistent authentication handling",
    "Built-in error handling and retries",
    "Clean abstraction from Google Drive API complexity"
  ]
}
```

**Response (With Processing - Optional):**
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
  "sync_only": false,
  "processing_note": null
}
```

### Sync Rental Contracts from Google Drive
```http
GET /api/v1/mcp/gdrive/rental-contracts
Authorization: Bearer <token>
```

**Query Parameters:**
- `query`: Search query for rental contract files (default: "rental")
- `process_files`: Whether to automatically process found rental contracts (default: false)
- `user_id`: User ID for contract processing (only required if process_files=true)

**Response (Sync Only - Default):**
```json
{
  "status": "success",
  "message": "Successfully synced 2 rental contract files from Google Drive",
  "contracts": [
    {
      "file_id": "1XYZ789...",
      "name": "Rental Agreement - Main Street.pdf",
      "mime_type": "application/pdf",
      "gdrive_uri": "gdrive:///1XYZ789..."
    }
  ],
  "total_count": 2,
  "processed_count": 0,
  "sync_only": true,
  "processing_note": "Contracts are synced only. Use POST /api/v1/orchestrator/workflow/invoice/start to process contracts and generate invoices.",
  "contract_type_focus": "rental_lease",
  "rental_specific_features": [
    "Enhanced filtering for rental/lease keywords",
    "Optimized search for property-related documents",
    "Automatic contract_type classification as rental_lease"
  ]
}
```

### MCP Webhook (for real-time sync)
```http
POST /api/v1/mcp/gdrive/webhook
X-MCP-Signature: hmac-sha256-signature
```

---

## 👤 Human Input & Validation Endpoints

### Submit Human Input
```http
POST /human-input/submit
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "workflow_id": "uuid-123",
  "input_type": "validation_correction",
  "input_data": {
    "corrected_amount": 5000.00,
    "corrected_due_date": "2024-01-31",
    "notes": "Updated payment terms"
  }
}
```

### Get Human Input Requirements
```http
GET /human-input/request/{workflow_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "workflow_id": "uuid-123",
  "input_required": true,
  "input_type": "validation_correction",
  "prompt": "Please review and correct the extracted contract information",
  "data_to_review": {
    "amount": null,
    "due_date": "unclear",
    "payment_terms": "needs clarification"
  },
  "suggestions": [...],
  "expires_at": "2024-01-01T01:00:00Z"
}
```

### Get Validation Requirements
```http
GET /validation/requirements/{workflow_id}
Authorization: Bearer <token>
```

### Resume Workflow After Human Input
```http
POST /validation/resume
Authorization: Bearer <token>
```

---

## 📄 Document Management Endpoints

### Upload Document
```http
POST /documents/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

### Bulk Document Upload
```http
POST /documents/upload/bulk
Authorization: Bearer <token>
```

### Get Document
```http
GET /documents/{document_id}
Authorization: Bearer <token>
```

### Delete Document
```http
DELETE /documents/{document_id}
Authorization: Bearer <token>
```

### Process Document
```http
POST /documents/{document_id}/process
Authorization: Bearer <token>
```

---

## 💰 Invoice Management Endpoints

### List Invoices
```http
GET /invoices/database/list
Authorization: Bearer <token>
```

**Query Parameters:**
- `user_id`: Filter by user
- `status`: Filter by status
- `limit`: Number of results (default: 50)
- `offset`: Pagination offset

### Get Invoice Details
```http
GET /invoices/database/{invoice_id}
Authorization: Bearer <token>
```

### Get Invoice by Workflow
```http
GET /invoices/database/workflow/{workflow_id}
Authorization: Bearer <token>
```

### Create Invoice
```http
POST /invoices/create_invoice
Authorization: Bearer <token>
```

### Approve Invoice
```http
POST /invoices/approve_invoice
Authorization: Bearer <token>
```

### Get Invoice Templates
```http
GET /invoices/database/templates
Authorization: Bearer <token>
```

### Get Adaptive UI Designs
```http
GET /invoices/{invoice_id}/adaptive-ui-designs
Authorization: Bearer <token>
```

---

## 📅 Invoice Scheduling Endpoints

### Create Schedule
```http
POST /schedules
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "contract_id": "cont-123",
  "frequency": "monthly",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "amount": 5000.00,
  "currency": "USD"
}
```

### Search Schedules
```http
GET /schedules/search
Authorization: Bearer <token>
```

### Get Schedules by Date
```http
GET /schedules/date/{target_date}
Authorization: Bearer <token>
```

### Process Scheduled Invoices
```http
POST /process-scheduled-invoices
Authorization: Bearer <token>
```

### Create Sample Schedules
```http
POST /schedules/create-samples
Authorization: Bearer <token>
```

---

## 🎨 Template Management Endpoints

### List Templates
```http
GET /templates/
Authorization: Bearer <token>
```

### Get Template
```http
GET /templates/{template_id}
Authorization: Bearer <token>
```

### Preview Template
```http
POST /templates/preview
Authorization: Bearer <token>
```

### Generate PDF from Template
```http
POST /templates/generate-pdf
Authorization: Bearer <token>
```

### Validate Template
```http
POST /templates/{template_id}/validate
Authorization: Bearer <token>
```

### Get Sample Data
```http
GET /templates/{template_id}/sample-data
Authorization: Bearer <token>
```

---

## 🧠 LLM & Embeddings Endpoints

### Create Embedding
```http
POST /embeddings/create
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "text": "Contract text to embed",
  "model": "text-embedding-ada-002"
}
```

### Batch Create Embeddings
```http
POST /embeddings/create-batch
Authorization: Bearer <token>
```

### Store Embedding
```http
POST /embeddings/store
Authorization: Bearer <token>
```

### Search Embeddings
```http
POST /embeddings/search
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "query": "payment terms",
  "top_k": 5,
  "filter": {
    "user_id": "user123"
  }
}
```

### Get Embedding Stats
```http
GET /embeddings/stats
Authorization: Bearer <token>
```

### LLM Health Check
```http
GET /llm/health
Authorization: Bearer <token>
```

---

## 📧 Email & Communication Endpoints

### Send Email
```http
POST /emails/send-email
Authorization: Bearer <token>
```

### Send Scheduled Email
```http
POST /emails/scheduled-email/{recipient_email}
Authorization: Bearer <token>
```

---

## 🔧 System & Utility Endpoints

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "ok"
}
```

### Get System Status
```http
GET /status
Authorization: Bearer <token>
```

### Test Gmail Connection
```http
GET /gmail/test-connection
Authorization: Bearer <token>
```

### Get Gmail OAuth URL
```http
GET /gmail/oauth-url
Authorization: Bearer <token>
```

---

## 🧪 Testing & Evaluation Endpoints

### Run Contract Processing Evaluations
```http
POST /api/v1/contract-processing/run-evals
Authorization: Bearer <token>
```

### Test Single Contract Processing
```http
POST /api/v1/contract-processing/test-single
Authorization: Bearer <token>
```

### Extract Invoice Data (Test)
```http
GET /api/v1/contract-processing/extract-invoice/{user_id}/{contract_name}
Authorization: Bearer <token>
```

### Batch Test Contracts
```http
POST /api/v1/contract-processing/batch-test
Authorization: Bearer <token>
```

---

# 🔄 Workflow Examples

## Complete Contract-to-Invoice Workflow

### 1. Start Agentic Workflow
```bash
curl -X POST "http://localhost:8000/api/v1/orchestrator/workflow/invoice/start" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "user_id=user123" \
  -F "contract_name=service-agreement.pdf" \
  -F "max_attempts=3" \
  -F "options={}" \
  -F "contract_file=@/path/to/contract.pdf"
```

### 2. Monitor Workflow Progress
```bash
curl -X GET "http://localhost:8000/api/v1/orchestrator/workflow/uuid-123/status" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. Handle Human Input (if required)
```bash
# Check if human input is needed
curl -X GET "http://localhost:8000/human-input/request/uuid-123" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Submit human input
curl -X POST "http://localhost:8000/human-input/submit" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "uuid-123",
    "input_type": "validation_correction",
    "input_data": {
      "corrected_amount": 5000.00,
      "corrected_due_date": "2024-01-31"
    }
  }'
```

### 4. Get Generated Invoice
```bash
curl -X GET "http://localhost:8000/api/v1/orchestrator/workflow/uuid-123/invoice" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 5. Get UI Template
```bash
curl -X GET "http://localhost:8000/api/v1/orchestrator/workflow/uuid-123/ui-template" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Google Drive Integration Workflow

### 1. Sync Contracts from Google Drive (No Processing)
```bash
# Sync all contracts (default: sync only, no processing)
curl -X GET "http://localhost:8000/api/v1/mcp/gdrive/contracts" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Sync rental contracts specifically
curl -X GET "http://localhost:8000/api/v1/mcp/gdrive/rental-contracts" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Optional: Force processing during sync (not recommended for large files)
curl -X GET "http://localhost:8000/api/v1/mcp/gdrive/contracts?user_id=user123&process_files=true" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 1a. Start Agentic Workflow for Contract Processing
```bash
# After syncing, process a specific contract and generate invoice
curl -X POST "http://localhost:8000/api/v1/orchestrator/workflow/invoice/start" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "user_id=user123" \
  -F "contract_name=rental.pdf" \
  -F "contract_file=@/path/to/downloaded/rental.pdf"
```

### 2. Query Processed Contracts
```bash
curl -X POST "http://localhost:8000/contracts/query" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "contract_name": "Service Agreement.pdf",
    "query": "What are the payment terms and schedule?"
  }'
```

---

# 🚨 Error Handling

## Standard Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The provided data failed validation",
    "details": {
      "field": "amount",
      "issue": "Amount must be greater than 0"
    },
    "timestamp": "2024-01-01T00:00:00Z",
    "request_id": "req-123"
  }
}
```

## Common Error Codes

- `AUTHENTICATION_ERROR` (401): Invalid or missing authentication token
- `AUTHORIZATION_ERROR` (403): Insufficient permissions
- `VALIDATION_ERROR` (400): Request data validation failed
- `NOT_FOUND` (404): Requested resource not found
- `WORKFLOW_ERROR` (422): Workflow processing error
- `AGENT_ERROR` (500): Internal agent processing error
- `MCP_ERROR` (502): External MCP service error

---

# 📊 Rate Limits

- **Authentication endpoints**: 10 requests per minute per IP
- **File upload endpoints**: 5 requests per minute per user
- **Workflow endpoints**: 20 requests per minute per user
- **Query endpoints**: 100 requests per minute per user

---

# 🔗 Webhooks

## MCP Google Drive Webhook

When files change in Google Drive, the MCP server can send webhook notifications:

```json
{
  "file_id": "1ABC123...",
  "name": "Updated Contract.pdf",
  "mime_type": "application/pdf",
  "size": 1024000,
  "modified_time": "2023-12-01T10:00:00Z"
}
```

Headers include HMAC signature for security verification.

---

# 🏗️ Development & Testing

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/smart_invoice_scheduler

# Authentication
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256

# LLM Services
OPENAI_API_KEY=your-openai-key
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# MCP Integration
MCP_SHARED_SECRET=mcp-secret-key-2024

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-password
```

## Running the Server

```bash
# Development
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Testing

```bash
# Run all tests
pytest

# Run specific test category
pytest tests/test_agents.py
pytest tests/test_workflows.py
pytest tests/test_api.py

# Run with coverage
pytest --cov=. --cov-report=html
```

---

This API documentation provides comprehensive coverage of all endpoints and explains how the agentic workflow processes contracts into professional invoices. The multi-agent architecture ensures reliability, scalability, and high-quality results while maintaining human oversight when needed.