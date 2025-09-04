# 🔧 Setup Steps: Embedding Service & OAuth2

## ✅ Step 2: Fix Embedding Service - COMPLETED

The embedding service has been fixed! The issue was that `PineconeService` was trying to access `embedding_model` attribute, but `EmbeddingService` uses `model` instead.

### What was fixed:
- Updated `pinecone_service.py` to use `embed_query()` and `embed_documents()` methods
- Removed incorrect `embedding_model` attribute references
- Service now works correctly with Vertex AI embeddings

### Verification:
```bash
cd /home/ramsha/Documents/smart-invoice-scheduler/server
uv run python -c "
from services.pinecone_service import get_pinecone_service
service = get_pinecone_service()
health = service.health_check()
print('Health:', health['status'])
"
```

**Result: ✅ WORKING** - Pinecone service is now healthy and can create embeddings!

---

## 🔐 Step 4: Complete OAuth2 Flow

### Option A: Automated Setup (Recommended)

Run the automated OAuth2 setup script:

```bash
cd /home/ramsha/Documents/smart-invoice-scheduler/server
uv run python oauth2_setup.py
```

This script will:
1. ✅ Generate OAuth2 authorization URL
2. 🌐 Open browser automatically
3. 📡 Start local callback server on localhost:8080
4. ⏳ Wait for you to complete authorization
5. 🔄 Exchange authorization code for tokens
6. 📝 Automatically update .env file
7. 🧪 Test Gmail connection
8. 📧 Optionally send test email

### Option B: Manual Setup

If you prefer manual setup:

#### Step 1: Get Authorization URL
```bash
uv run python -c "
from services.gmail_mcp_service import get_gmail_mcp_service
service = get_gmail_mcp_service()
result = service.get_oauth_authorization_url()
print('Visit this URL:', result['authorization_url'])
"
```

#### Step 2: Visit URL and Authorize
1. Copy the URL from step 1
2. Visit it in your browser
3. Sign in with your Google account
4. Grant Gmail sending permissions
5. You'll be redirected to `http://localhost:8080/oauth2callback?code=...`
6. Copy the `code` parameter value

#### Step 3: Exchange Code for Tokens
```bash
uv run python -c "
import asyncio
from services.gmail_mcp_service import get_gmail_mcp_service

async def exchange_tokens():
    service = get_gmail_mcp_service()
    # Replace YOUR_CODE_HERE with the actual code
    result = await service.exchange_code_for_tokens('YOUR_CODE_HERE')
    print('Refresh Token:', result['refresh_token'])

asyncio.run(exchange_tokens())
"
```

#### Step 4: Update .env File
Add the refresh token to your `.env` file:
```bash
echo 'GOOGLE_REFRESH_TOKEN="your_refresh_token_here"' >> .env
```

#### Step 5: Test Connection
```bash
uv run python -c "
import asyncio
from services.gmail_mcp_service import get_gmail_mcp_service

async def test_gmail():
    service = get_gmail_mcp_service()
    result = await service.test_gmail_connection()
    print('Gmail Test:', result)

asyncio.run(test_gmail())
"
```

---

## 🧪 Verification: Test Complete System

After completing both steps, run the full system test:

```bash
cd /home/ramsha/Documents/smart-invoice-scheduler/server
uv run python setup_invoice_scheduler.py
```

Expected results:
- ✅ Service Connections: All healthy
- ✅ Sample Schedules: Created successfully  
- ✅ RAG Retrieval: Working with embeddings
- ✅ Email Generation: AI content creation working
- ✅ End-to-End Test: Complete workflow functional

---

## 🎯 Next Steps After OAuth2 Setup

1. **Test Email Sending:**
```bash
curl -X POST http://localhost:8000/invoice-scheduler/gmail/test-email \
  -H "Content-Type: application/json" \
  -d '{
    "to": "your-email@example.com",
    "subject": "Test from Invoice Scheduler",
    "body_html": "<h1>Success!</h1><p>OAuth2 is working!</p>"
  }'
```

2. **Create Production Schedules:**
```bash
curl -X POST http://localhost:8000/invoice-scheduler/schedules/create-samples
```

3. **Test RAG Search:**
```bash
curl "http://localhost:8000/invoice-scheduler/schedules/search?query=monthly%20invoices"
```

4. **Enable Cloud Scheduler API:**
```bash
gcloud services enable cloudscheduler.googleapis.com --project=arcane-storm-443513-r8
```

5. **Deploy Gmail MCP Server:**
```bash
cd deployment && ./deploy_gmail_mcp.sh
```

---

## 📊 System Status Check

To verify everything is working:

```bash
curl http://localhost:8000/invoice-scheduler/status
```

Should show:
- ✅ Pinecone: healthy
- ✅ Gmail: connected  
- ✅ Agent: working
- ⚠️ Cloud Scheduler: needs API enablement

---

## 🎉 Success Indicators

You'll know everything is working when:

1. **Embedding Service:** `health_check()` returns "healthy"
2. **Gmail OAuth2:** `test_gmail_connection()` returns email address
3. **Email Sending:** Test emails arrive in your inbox
4. **RAG Search:** Queries return relevant invoice schedules
5. **AI Generation:** Creates professional email content
6. **End-to-End:** Complete workflow processes schedules

**You're now ready for automated invoice scheduling!** 🚀