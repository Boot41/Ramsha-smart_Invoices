# Postman Testing Guide for Contract Processing

## Prerequisites

1. **Server Running**: Make sure your FastAPI server is running
2. **Environment Variables**: Ensure all required env vars are set:
   ```env
   PROJECT_ID=your-google-cloud-project
   GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
   PINECONE_API_KEY=your-pinecone-api-key
   PINECONE_INDEX_NAME=smart-invoice-contracts
   ```

## Test Data

### Sample Contract PDF
Create a simple PDF from the text in `test_data/sample_contract.txt` or use any contract PDF you have.

## Postman Collection

### 1. Health Check
**GET** `http://localhost:8000/contracts/health`

**Headers:**
```
Content-Type: application/json
```

**Expected Response:**
```json
{
  "status": "healthy",
  "message": "✅ Contract processing service is running",
  "services": {
    "contract_processor": "available",
    "contract_rag_service": "available",
    "embedding_service": "available"
  },
  "timestamp": "2024-01-01T12:00:00"
}
```

### 2. Process Contract PDF
**POST** `http://localhost:8000/contracts/upload-and-process`

**Headers:**
```
Content-Type: multipart/form-data
```

**Body (form-data):**
- `file`: [Upload your PDF file]
- `user_id`: `test_user_123`

**Expected Response:**
```json
{
  "status": "success",
  "message": "✅ Contract processed successfully",
  "contract_name": "sample_contract.pdf",
  "user_id": "test_user_123",
  "total_chunks": 8,
  "total_embeddings": 8,
  "vector_ids": ["contract_test_user_123_abc123_0", "contract_test_user_123_abc123_1"],
  "text_preview": "SERVICE AGREEMENT This Service Agreement...",
  "processing_timestamp": "2024-01-01T12:00:00"
}
```

### 3. Generate Invoice Data
**POST** `http://localhost:8000/contracts/generate-invoice-data`

**Headers:**
```
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
  "user_id": "test_user_123",
  "contract_name": "sample_contract.pdf",
  "query": "Extract all invoice data including parties, payment terms, services, and billing schedule",
  "specific_requirements": [
    "payment_amounts",
    "billing_frequency", 
    "party_details",
    "service_descriptions"
  ]
}
```

**Expected Response:**
```json
{
  "status": "success",
  "message": "✅ Invoice data generated successfully",
  "contract_name": "sample_contract.pdf",
  "user_id": "test_user_123",
  "invoice_data": {
    "contract_title": "SERVICE AGREEMENT",
    "contract_type": "service_agreement",
    "contract_number": "DME-2024-001",
    "client": {
      "name": "TechCorp Solutions Inc.",
      "email": "billing@techcorp.com",
      "address": "123 Business Avenue, San Francisco, CA 94105",
      "phone": "(555) 123-4567",
      "tax_id": "12-3456789",
      "role": "client"
    },
    "service_provider": {
      "name": "Digital Marketing Experts LLC",
      "email": "invoices@digitalexperts.com",
      "address": "456 Marketing Street, New York, NY 10001",
      "phone": "(555) 987-6543",
      "tax_id": "98-7654321",
      "role": "service_provider"
    },
    "start_date": "2024-02-01",
    "end_date": "2025-01-31",
    "effective_date": "2024-01-15",
    "payment_terms": {
      "amount": 8500.00,
      "currency": "USD",
      "frequency": "monthly",
      "due_days": 30,
      "late_fee": 2.00,
      "discount_terms": null
    },
    "services": [
      {
        "description": "Digital marketing consulting services",
        "quantity": 20,
        "unit_price": 150.00,
        "total_amount": 8500.00,
        "unit": "hours"
      },
      {
        "description": "Social media management",
        "quantity": 1,
        "unit_price": null,
        "total_amount": null,
        "unit": "monthly"
      }
    ],
    "invoice_frequency": "monthly",
    "first_invoice_date": "2024-02-01",
    "next_invoice_date": "2024-02-01",
    "special_terms": "Late fees apply after 5 day grace period",
    "notes": "Quarterly business reviews included"
  },
  "confidence_score": 0.85,
  "generated_at": "2024-01-01T12:00:00"
}
```

### 4. Query Contract
**POST** `http://localhost:8000/contracts/query`

**Headers:**
```
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
  "user_id": "test_user_123",
  "contract_name": "sample_contract.pdf",
  "query": "What are the payment terms and when are invoices due?"
}
```

**Expected Response:**
```json
{
  "status": "success",
  "response": "According to the contract, the payment terms are as follows: Monthly retainer fee of $8,500 USD, payment is due Net 30 days from invoice date, and there's a 2% per month late payment fee on overdue amounts. Monthly invoices are sent on the 1st of each month with payment due 30 days from the invoice date.",
  "contract_name": "sample_contract.pdf",
  "user_id": "test_user_123",
  "query": "What are the payment terms and when are invoices due?",
  "generated_at": "2024-01-01T12:00:00"
}
```

### 5. Complete Workflow
**POST** `http://localhost:8000/contracts/process-and-generate-invoice`

**Headers:**
```
Content-Type: multipart/form-data
```

**Body (form-data):**
- `file`: [Upload your PDF file]
- `user_id`: `test_user_456`

**Expected Response:**
```json
{
  "status": "success",
  "message": "✅ Contract processed and invoice data generated successfully",
  "contract_processing": {
    "status": "success",
    "message": "✅ Contract processed successfully",
    "contract_name": "sample_contract.pdf",
    "user_id": "test_user_456",
    "total_chunks": 8,
    "total_embeddings": 8,
    "vector_ids": ["contract_test_user_456_def456_0"],
    "text_preview": "SERVICE AGREEMENT This Service Agreement...",
    "processing_timestamp": "2024-01-01T12:00:00"
  },
  "invoice_generation": {
    "status": "success",
    "message": "✅ Invoice data generated successfully",
    "contract_name": "sample_contract.pdf",
    "user_id": "test_user_456",
    "invoice_data": { /* ... same structure as above ... */ },
    "confidence_score": 0.85,
    "generated_at": "2024-01-01T12:00:00"
  },
  "workflow_completed_at": "2024-01-01T12:00:00"
}
```

## Testing Different Scenarios

### Test Cases to Try:

1. **Valid PDF Contract**
   - Use the sample contract above converted to PDF
   - Should return structured invoice data

2. **Empty or Invalid File**
   - Upload empty file or non-PDF
   - Should return 400 error with appropriate message

3. **Large Contract PDF**
   - Test with multi-page contracts
   - Verify chunking and processing works

4. **Different Contract Types**
   - Rental agreements
   - Consulting agreements  
   - Service contracts
   - Supply agreements

5. **Query Variations**
   - Ask about specific payment terms
   - Request party information
   - Query about dates and deadlines
   - Ask about services or deliverables

## Error Testing

### Common Errors to Test:

1. **Missing Environment Variables**
   - Remove PINECONE_API_KEY temporarily
   - Should get initialization errors

2. **Invalid User ID**
   - Try querying non-existent contracts
   - Should get 404 errors

3. **Malformed Requests**
   - Send invalid JSON
   - Missing required fields
   - Should get 400 errors

## Environment Variables for Testing

Create a `.env.test` file:
```env
PROJECT_ID=your-test-project
GOOGLE_APPLICATION_CREDENTIALS=/path/to/test-service-account.json
PINECONE_API_KEY=your-test-pinecone-key
PINECONE_INDEX_NAME=test-contracts
```

## Performance Testing

- **Small Contract**: < 5 pages, should process in 10-20 seconds
- **Medium Contract**: 5-20 pages, should process in 20-40 seconds  
- **Large Contract**: 20+ pages, may take 1-2 minutes

## Troubleshooting

### Common Issues:

1. **"No documents found"** - Contract not processed yet
2. **"Failed to initialize model"** - Check GCP credentials
3. **"Failed to store vectors"** - Check Pinecone configuration
4. **"Failed to extract text"** - PDF might be image-based or corrupted

### Debug Steps:

1. Check server logs for detailed error messages
2. Verify all environment variables are set
3. Test health endpoint first
4. Start with small, simple contracts
5. Check Pinecone dashboard for stored vectors