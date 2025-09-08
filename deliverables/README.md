# Smart Invoice Scheduler - Project Documentation
## Video Demo of the product
https://www.loom.com/share/a786f9466e854f38ad5fc18a66fa0d7c?sid=350bf5b8-22ff-45b9-89e8-240f28a1c097

## Project Link
https://smart-invoice-scheduler-410805250566.us-central1.run.app/dashboard

## 🚀 Project Overview

Smart Invoice Scheduler is an AI-powered platform that automates contract processing and intelligent invoice generation. The application leverages a sophisticated **Google ADK-based agentic workflow** to orchestrate contract analysis, data validation, invoice creation, and scheduling. This ensures a high degree of accuracy and automation, with built-in support for human-in-the-loop corrections.

## 🎯 Key Features

### 🤖 Google ADK Agentic Workflow
- **Multi-Agent Orchestration**: A robust pipeline of specialized agents handles the end-to-end invoice processing lifecycle.
- **Human-in-the-Loop**: The workflow automatically pauses for human validation when data is uncertain, ensuring accuracy.
- **Event-Driven & Resumable**: Workflows can be paused and resumed, providing flexibility and reliability.
- **Real-time Progress Tracking**: Monitor the status of each agent and the overall workflow progress via API.

### 🔍 Contract Processing & Analysis
- **PDF & GDrive Integration**: Process contracts from direct uploads or Google Drive.
- **AI-Powered RAG**: Retrieval-Augmented Generation for deep contract understanding and data extraction.
- **Unified Data Model**: All extracted data is converted to a canonical `UnifiedInvoiceData` format.

### 📊 Invoice Generation & Management
- **Automated Invoice Creation**: Generate structured invoice data directly from the agentic workflow.
- **Template-Based UI Generation**: Create professional HTML/CSS invoices from corrected data.
- **Data Correction & Finalization**: A dedicated agent applies business rules and human feedback to produce final invoice JSON.

### 🗓️ Intelligent Scheduling
- **RAG-Based Schedule Retrieval**: Automatically discover and apply recurring payment schedules from contract text.
- **Google Cloud Scheduler Integration**: Create and manage recurring invoice jobs for automated generation.

## 🏗️ System Architecture

The system is built on a modern stack, with a React frontend and a FastAPI backend. The core innovation lies in the backend's **Google ADK-based agentic workflow**.

### Backend (FastAPI + Python + Google ADK)
- **Framework**: FastAPI with Google Agent Development Kit (ADK)
- **AI Workflow**: A sequence of specialized agents for contract processing, validation, correction, and generation.
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Vector DB**: Pinecone for RAG-based embeddings
- **Scheduling**: Google Cloud Scheduler for recurring jobs

## 🤖 AI-Powered Features

The AI capabilities are organized into a multi-step agentic workflow:

1.  **ContractProcessingADKAgent**: Ingests documents, creates vector embeddings, and uses RAG to extract an initial `UnifiedInvoiceData` object.
2.  **ValidationADKAgent**: Audits the extracted data. If confidence is low, it pauses the workflow and requests human review.
3.  **CorrectionADKAgent**: Merges human feedback with the extracted data to create a final, validated invoice JSON.
4.  **InvoiceGeneratorADKAgent**: Persists the final invoice record in the database.
5.  **UIGenerationADKAgent**: Produces a polished HTML/CSS invoice for viewing.
6.  **ScheduleRetrievalADKAgent**: Analyzes the contract to find recurring payment patterns and schedules future invoices.

## 🛠️ API Endpoints

The API has been updated with a dedicated set of endpoints to manage the ADK agentic workflows.

### ADK Agentic Workflow Endpoints
```http
# Start a new workflow
POST /adk/workflow/invoice/start

# Start a workflow for an existing contract
POST /adk/workflow/invoice/start-for-contract

# Get the status of a workflow
GET /adk/workflow/{workflow_id}/status

# Resume a paused workflow with human input
POST /adk/workflow/{workflow_id}/resume

# Get the final invoice data from a completed workflow
GET /adk/workflow/{workflow_id}/invoice

# Get the human input requirements for a paused workflow
GET /adk/workflow/{workflow_id}/human-input-request

# Cancel a running workflow
DELETE /adk/workflow/{workflow_id}/cancel
```

## 📋 Core Schema Models

### UnifiedInvoiceData
The canonical data model used throughout the ADK agentic workflow.

```python
class UnifiedInvoiceData(BaseModel):
    # Metadata
    metadata: UnifiedInvoiceMetadata

    # Parties
    client: Optional[ContractParty] = None
    service_provider: Optional[ContractParty] = None

    # Invoice Details
    invoice_id: Optional[str] = None
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None

    # Payment Information
    payment_terms: Optional[PaymentTerms] = None
    totals: Optional[UnifiedInvoiceTotals] = None

    # Service Details
    service_details: Optional[ServiceDetails] = None
```

## 🚦 Getting Started

### Prerequisites
- Node.js 18+ for frontend
- Python 3.9+ for backend
- PostgreSQL 13+
- Pinecone API key
- Google Cloud credentials (for GCS and Cloud Scheduler)

### Backend Setup
```bash
cd server
# Install dependencies
pip install -r requirements.txt

# Run the FastAPI server
python main.py
```

## 📁 Project Structure

```
smart-invoice-scheduler/
├── client/                          # React frontend
└── server/                          # FastAPI backend
    ├── adk_agents/                 # Google ADK Agent implementations
    ├── models/                     # SQLAlchemy database models
    ├── routes/                     # API route handlers (including adk_orchestrator.py)
    ├── services/                   # Business logic services
    ├── schemas/                    # Pydantic schemas (including unified_invoice_schemas.py)
    └── main.py                     # FastAPI application entry point
```

---

*This documentation provides a comprehensive overview of the Smart Invoice Scheduler platform, highlighting the new Google ADK-based agentic workflow. For more details, refer to `deliverables/ARCHITECTURE.md`.*
