# Contract Processing Setup Guide

This document explains how to set up and use the contract processing functionality for generating invoice data from contract PDFs.

## Environment Variables Required

Add these to your `.env` file:

```env
# Google Cloud / Vertex AI Configuration
PROJECT_ID=your-google-cloud-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account-key.json

# Pinecone Vector Database Configuration
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_INDEX_NAME=smart-invoice-contracts
```

## Pinecone Index Setup

1. Create a Pinecone account at https://pinecone.io
2. Create a new index with the following specifications:
   - **Index Name**: `smart-invoice-contracts` (or update `PINECONE_INDEX_NAME`)
   - **Dimensions**: `768` (for Google Vertex AI text-embedding-004)
   - **Metric**: `cosine`
   - **Pod Type**: `s1.x1` (starter tier)

## API Endpoints

### 1. Process Contract PDF

```http
POST /contracts/upload-and-process
Content-Type: multipart/form-data

file: contract.pdf (PDF file)
user_id: string (user identifier)
```

**Response:**
```json
{
  "status": "success",
  "message": "✅ Contract processed successfully",
  "contract_name": "contract.pdf",
  "user_id": "user123",
  "total_chunks": 15,
  "total_embeddings": 15,
  "vector_ids": ["vector_id_1", "vector_id_2", ...],
  "text_preview": "Contract text preview...",
  "processing_timestamp": "2024-01-01T12:00:00"
}
```

### 2. Generate Invoice Data

```http
POST /contracts/generate-invoice-data
Content-Type: application/json

{
  "user_id": "user123",
  "contract_name": "contract.pdf",
  "query": "Extract invoice data and payment terms",
  "specific_requirements": ["payment_schedule", "parties", "amounts"]
}
```

**Response:**
```json
{
  "status": "success",
  "message": "✅ Invoice data generated successfully",
  "contract_name": "contract.pdf",
  "user_id": "user123",
  "invoice_data": {
    "contract_title": "Service Agreement",
    "contract_type": "service_agreement",
    "client": {
      "name": "Client Company",
      "email": "client@example.com",
      "role": "client"
    },
    "service_provider": {
      "name": "Service Provider LLC",
      "email": "provider@example.com", 
      "role": "service_provider"
    },
    "payment_terms": {
      "amount": 5000.00,
      "currency": "USD",
      "frequency": "monthly",
      "due_days": 30
    },
    "services": [
      {
        "description": "Consulting services",
        "quantity": 40,
        "unit_price": 125.00,
        "total_amount": 5000.00,
        "unit": "hours"
      }
    ],
    "invoice_frequency": "monthly",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31"
  },
  "confidence_score": 0.85,
  "generated_at": "2024-01-01T12:00:00"
}
```

### 3. Complete Workflow

```http
POST /contracts/process-and-generate-invoice
Content-Type: multipart/form-data

file: contract.pdf (PDF file)
user_id: string (user identifier)
```

This endpoint combines both processing and invoice generation in a single call.

### 4. Query Contract

```http
POST /contracts/query
Content-Type: application/json

{
  "user_id": "user123",
  "contract_name": "contract.pdf",
  "query": "What are the payment terms?"
}
```

## Data Models

### ContractInvoiceData Structure

The generated invoice data follows this structure:

- **Contract Information**: title, type, number, dates
- **Parties**: client and service provider details
- **Payment Terms**: amounts, frequency, due dates, fees
- **Services**: itemized services with quantities and prices
- **Invoice Schedule**: frequency and dates
- **Metadata**: confidence scores and timestamps

### Supported Contract Types

- `service_agreement`
- `rental_lease`
- `maintenance_contract`
- `supply_contract`
- `consulting_agreement`
- `other`

### Invoice Frequencies

- `monthly`
- `quarterly`
- `biannually`
- `annually`
- `one_time`
- `custom`

## Usage Flow

1. **Upload Contract**: Use the `/upload-and-process` endpoint to process a PDF
2. **Generate Invoice Data**: Use `/generate-invoice-data` to extract structured data
3. **Query for Details**: Use `/query` for specific questions about the contract
4. **Or Use Complete Workflow**: Use `/process-and-generate-invoice` for one-step processing

## Error Handling

All endpoints return appropriate HTTP status codes:
- `200`: Success
- `400`: Bad request (invalid file, missing data)
- `404`: Contract not found
- `500`: Server error

Error responses include detailed error messages for debugging.

## Performance Notes

- PDF processing time depends on document size
- Vector embedding generation scales with text length
- Typical processing time: 10-30 seconds for average contracts
- Use health check endpoint `/contracts/health` to verify service status