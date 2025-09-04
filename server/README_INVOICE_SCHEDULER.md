# Invoice Scheduler Agent with RAG & Gmail MCP

A comprehensive agentic workflow system that automates invoice scheduling using:
- **RAG (Retrieval-Augmented Generation)** with Pinecone vector database
- **Gmail MCP Server** for automated email sending
- **Google Cloud Scheduler** for real-time scheduling
- **Gemini AI** for intelligent email content generation

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Client    │    │   FastAPI Server │    │  Gmail MCP      │
│                 │◄──►│                  │◄──►│  (Cloud Run)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │ Invoice Scheduler│
                       │     Agent        │
                       └──────────────────┘
                                │
                  ┌─────────────┼─────────────┐
                  ▼             ▼             ▼
         ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
         │  Pinecone   │ │   Gemini    │ │   Cloud     │
         │  Vector DB  │ │     AI      │ │  Scheduler  │
         └─────────────┘ └─────────────┘ └─────────────┘
```

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Ensure you're in the server directory
cd /home/ramsha/Documents/smart-invoice-scheduler/server

# Install dependencies
pip install -e .

# Verify environment variables in .env
cat .env
```

### 2. Run Comprehensive Setup

```bash
# Run the automated setup script
python setup_invoice_scheduler.py
```

This will:
- ✅ Test all service connections
- 🚀 Prepare Gmail MCP server deployment
- 🔐 Generate OAuth2 setup instructions
- 📝 Create sample invoice schedules
- 🔍 Test RAG retrieval functionality
- ✉️ Test AI email generation
- ⏰ Configure Cloud Scheduler
- 🧪 Run end-to-end workflow test

### 3. Deploy Gmail MCP Server

```bash
# Deploy to Google Cloud Run
cd deployment
./deploy_gmail_mcp.sh

# Update .env with the deployed URL
echo "GMAIL_MCP_SERVER_URL=https://your-service-url" >> ../.env
```

### 4. Complete OAuth2 Setup

```bash
# Get OAuth authorization URL
curl http://localhost:8000/invoice-scheduler/gmail/oauth-url

# Visit the URL, authorize, and get the authorization code
# Then exchange it for tokens (replace YOUR_CODE with actual code):
curl -X POST http://localhost:8000/invoice-scheduler/gmail/exchange-code \
  -H "Content-Type: application/json" \
  -d '{"authorization_code": "YOUR_CODE"}'

# Add the refresh token to .env
echo "GOOGLE_REFRESH_TOKEN=your_refresh_token_here" >> .env
```

## 📡 API Endpoints

### Core Functionality

#### Get System Status
```bash
GET /invoice-scheduler/status
```

#### Process Scheduled Invoices (Called by Cloud Scheduler)
```bash
POST /invoice-scheduler/process-scheduled-invoices
{
  "target_date": "2024-09-15",
  "triggered_by": "cloud_scheduler"
}
```

### Schedule Management

#### Create Invoice Schedules
```bash
POST /invoice-scheduler/schedules
[
  {
    "recipient_email": "client@example.com",
    "send_dates": ["2024-09-15", "2024-10-15"],
    "frequency": "monthly",
    "invoice_template": "modern",
    "amount": 2500.00,
    "client_name": "Acme Corporation",
    "service_description": "Web Development Services",
    "due_days": 30
  }
]
```

#### Search Schedules with Natural Language
```bash
GET /invoice-scheduler/schedules/search?query=monthly%20web%20development%20invoices
```

#### Get Schedules by Date
```bash
GET /invoice-scheduler/schedules/date/2024-09-15
```

### Gmail Integration

#### Test Email Sending
```bash
POST /invoice-scheduler/gmail/test-email
{
  "to": "test@example.com",
  "subject": "Test Invoice Email",
  "body_html": "<h1>Test</h1><p>This is a test invoice email.</p>"
}
```

#### Test Gmail Connection
```bash
GET /invoice-scheduler/gmail/test-connection
```

### Cloud Scheduler Management

#### Create Recurring Schedule
```bash
POST /invoice-scheduler/scheduler/recurring
{
  "client_name": "Acme Corporation",
  "frequency": "monthly",
  "start_date": "2024-09-15",
  "hour": 9,
  "minute": 0
}
```

#### List Scheduled Jobs
```bash
GET /invoice-scheduler/scheduler/jobs
```

#### Control Jobs
```bash
POST /invoice-scheduler/scheduler/jobs/{job_name}/pause
POST /invoice-scheduler/scheduler/jobs/{job_name}/resume
POST /invoice-scheduler/scheduler/jobs/{job_name}/run
DELETE /invoice-scheduler/scheduler/jobs/{job_name}
```

## 🧪 Testing Workflow

### 1. Create Sample Data
```bash
curl -X POST http://localhost:8000/invoice-scheduler/schedules/create-samples
```

### 2. Test RAG Retrieval
```bash
curl "http://localhost:8000/invoice-scheduler/schedules/search?query=monthly%20invoices&top_k=5"
```

### 3. Test Email Generation
```bash
curl -X POST http://localhost:8000/invoice-scheduler/process-scheduled-invoices \
  -H "Content-Type: application/json" \
  -d '{"target_date": "2024-09-05"}'
```

### 4. Test Real Email Sending (requires OAuth setup)
```bash
curl -X POST http://localhost:8000/invoice-scheduler/gmail/test-email \
  -H "Content-Type: application/json" \
  -d '{
    "to": "your-email@example.com",
    "subject": "Test Invoice from Scheduler",
    "body_html": "<h2>Invoice Test</h2><p>This is a test invoice email from the automated scheduler.</p>"
  }'
```

## 🔧 Configuration

### Environment Variables (.env)

```bash
# GCP Configuration
PROJECT_ID='your-gcp-project-id'
GOOGLE_APPLICATION_CREDENTIALS='./details/credentials.json'
GOOGLE_API_KEY='your-gemini-api-key'

# OAuth Credentials
GOOGLE_CLIENT_ID="your-client-id"
GOOGLE_CLIENT_SECRET="your-client-secret"
GOOGLE_REFRESH_TOKEN="your-refresh-token"  # Obtained via OAuth flow

# Pinecone Configuration
PINECONE_API_KEY='your-pinecone-api-key'
PINECONE_INDEX_NAME='contracts'

# Gmail MCP Server (set after deployment)
GMAIL_MCP_SERVER_URL='https://your-gmail-mcp-service-url'

# Database
DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/smart_invoice_scheduler"
```

### Supported Invoice Frequencies
- `daily`: Every day at specified time
- `weekly`: Every week on the same day
- `monthly`: Every month on the same date
- `quarterly`: Every 3 months on the same date

### Supported Invoice Templates
- `modern`: Clean gradient design
- `vintage`: Classic professional style
- `minimalist`: Ultra-clean typography focused

## 📊 Monitoring & Logging

### Health Checks
```bash
# Overall system health
GET /health

# Invoice scheduler specific status
GET /invoice-scheduler/status
```

### Logging
All operations are logged with structured logging:
- 📝 Schedule creation and retrieval
- 🔍 RAG query processing  
- ✉️ Email generation and sending
- ⏰ Scheduler job execution
- ❌ Error handling and recovery

### Cloud Scheduler Monitoring
- Jobs are visible in Google Cloud Console
- Execution history and logs available
- Automatic retry on failures
- Email notifications for job failures

## 🔒 Security Features

### Authentication
- OAuth2 flow for Gmail access
- Service account authentication for GCP
- API key authentication for Pinecone and Gemini

### Data Protection
- Sensitive data encrypted in Pinecone metadata
- OAuth tokens securely stored in Cloud Secrets
- No email content stored permanently
- HTTPS enforced for all API communications

### Access Control
- Cloud IAM roles for service accounts
- Gmail API scope limited to sending only
- Pinecone namespace isolation
- Rate limiting on API endpoints

## 🛠️ Development

### Running in Development Mode
```bash
# Start the FastAPI server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run tests
python -m pytest tests/

# Test individual components
python agents/invoice_scheduler_agent.py
python services/gmail_mcp_service.py
python services/cloud_scheduler_service.py
```

### Adding New Features

1. **New Invoice Templates**: Add to client/src/components/invoices/
2. **New Frequency Types**: Update `_generate_cron_schedule()` in CloudSchedulerService
3. **Custom Email Templates**: Modify `generate_invoice_email_content()` in InvoiceSchedulerAgent
4. **Additional Metadata**: Update InvoiceSchedule dataclass and Pinecone ingestion

## 📈 Scaling Considerations

### Performance
- Pinecone handles millions of vectors efficiently
- Cloud Scheduler supports thousands of jobs
- Gmail API has daily sending limits (check quotas)
- FastAPI auto-scales with container orchestration

### Reliability
- Cloud Scheduler automatic retries
- Pinecone built-in redundancy  
- Gmail API rate limiting with backoff
- Database connection pooling

### Cost Optimization
- Cloud Scheduler: Pay per job execution
- Pinecone: Serverless usage-based pricing
- Gmail MCP: Cloud Run pay-per-request
- Gemini API: Pay-per-token pricing

## 🆘 Troubleshooting

### Common Issues

#### OAuth2 Setup Issues
```bash
# Check OAuth configuration
curl http://localhost:8000/invoice-scheduler/gmail/oauth-url

# Verify credentials in .env
grep GOOGLE_ .env
```

#### Pinecone Connection Issues
```bash
# Test Pinecone directly
python -c "from services.pinecone_service import get_pinecone_service; print(get_pinecone_service().health_check())"
```

#### Cloud Scheduler Permission Issues
```bash
# Check service account permissions
gcloud projects get-iam-policy $PROJECT_ID --flatten="bindings[].members" --filter="bindings.members:*@*.iam.gserviceaccount.com"
```

#### Gmail MCP Server Issues
```bash
# Check Cloud Run deployment
gcloud run services describe gmail-mcp-server --region=us-central1

# View logs
gcloud run services logs read gmail-mcp-server --region=us-central1
```

### Getting Support

1. Check the setup results: `cat setup_results.json`
2. View application logs: `tail -f smart_invoice_scheduler.log`
3. Test individual components using the CLI interfaces
4. Verify all environment variables are set correctly
5. Ensure GCP project has required APIs enabled

## 🎯 Production Deployment Checklist

- [ ] All environment variables configured
- [ ] Gmail MCP server deployed to Cloud Run
- [ ] OAuth2 flow completed and refresh token saved
- [ ] Sample schedules created and tested
- [ ] RAG retrieval working with real data
- [ ] Email sending tested with real recipients
- [ ] Cloud Scheduler jobs configured
- [ ] Monitoring and alerting set up
- [ ] Error handling and retry logic tested
- [ ] Security review completed
- [ ] Performance testing done
- [ ] Backup and recovery procedures documented

---

🎉 **Your Invoice Scheduler Agent is now ready for automated, intelligent invoice management!**