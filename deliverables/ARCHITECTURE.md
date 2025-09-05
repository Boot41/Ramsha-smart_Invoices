# System Architecture

## 🏗️ Architecture Overview

Smart Invoice Scheduler follows a modern microservices architecture with clear separation of concerns between the frontend, backend, and AI processing services. The recent introduction of the **Google Agent Development Kit (ADK)** has evolved the AI processing layer into a sophisticated agentic workflow.

```
┌─────────────────────────────────────────────────────────────────┐
│                          Frontend Layer                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │
│  │   React UI  │  │ State Mgmt  │  │  Routing    │               │
│  │  Components │  │  (Zustand)  │  │ (React Rtr) │               │
│  └─────────────┘  └─────────────┘  └─────────────┘               │
└─────────────────────────────────────────────────────────────────┘
                                │
                           HTTP/HTTPS
                                │
┌─────────────────────────────────────────────────────────────────┐
│                         API Gateway Layer                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │
│  │  FastAPI    │  │ Middleware  │  │   ADK Routes  │               │
│  │  Routes     │  │ Auth/Logs   │  │ (/adk/*)    │               │
│  └─────────────┘  └─────────────┘  └─────────────┘               │
└─────────────────────────────────────────────────────────────────┘
                                │
                        Service Layer
                                │
┌─────────────────────────────────────────────────────────────────┐
│                     ADK Agentic Workflow Layer                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │
│  │ Orchestrator│  │  Contract   │  │ Validation  │               │
│  │  Workflow   │  │  Processor  │  │    Agent    │               │
│  └─────────────┘  └─────────────┘  └─────────────┘               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │
│  │ Correction  │  │  Invoice    │  │ UI & Sched. │               │
│  │    Agent    │  │  Generator  │  │   Agents    │               │
│  └─────────────┘  └─────────────┘  └─────────────┘               │
└─────────────────────────────────────────────────────────────────┘
                                │
                        Data Access Layer
                                │
┌─────────────────────────────────────────────────────────────────┐
│                         Data Layer                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │
│  │ PostgreSQL  │  │  Pinecone   │  │    GCS      │               │
│  │  Database   │  │  Vector DB  │  │File Storage │               │
│  └─────────────┘  └─────────────┘  └─────────────┘               │
└─────────────────────────────────────────────────────────────────┘
```

## 🖥️ Frontend Architecture

(No significant changes in the new architecture)

### Component Hierarchy
```
App.tsx
├── Layout.tsx
│   ├── Navbar.tsx
│   └── Sidebar.tsx
├── Pages/
│   ├── Dashboard/
│   ├── Contracts/
│   │   └── ContractsList.tsx
│   ├── Invoices/
│   │   ├── InvoiceTemplates.tsx
│   │   ├── InvoicesList.tsx
│   │   └── InvoiceScheduling.tsx
│   └── Auth/
└── Components/
    ├── UI/ (Reusable components)
    └── Shared/ (Common components)
```

## 🔧 Backend Architecture

### ADK Agent-based Service Layer
The backend has transitioned to an agent-based architecture using the Google ADK. Business logic is encapsulated within a series of cooperating agents orchestrated by a main workflow.

```python
# ADK Agent Structure (adk_agents/)
├── orchestrator_adk_workflow.py    # Main workflow orchestrator
├── contract_processing_adk_agent.py # Ingestion, RAG
├── validation_adk_agents.py        # Business rule validation, human-in-the-loop
├── correction_adk_agent.py         # Data correction and finalization
├── invoice_generator_adk_agent.py  # Database record creation
├── ui_generation_adk_agent.py      # HTML invoice generation
└── schedule_retrieval_adk_agent.py # Automated scheduling
```

### API Route Organization
The API routes now include dedicated endpoints for managing the ADK agentic workflows.

```python
# Route Structure (routes/)
├── auth.py
├── contracts.py
├── invoices.py
├── adk_orchestrator.py  # <-- New ADK workflow endpoints
└── ...
```

## 🤖 AI Processing Architecture (ADK Agentic Workflow)

The AI processing has been re-architected into a sequential, event-driven workflow managed by the `InvoiceProcessingADKWorkflow`. Each step is handled by a specialized ADK agent.

### ADK Workflow Pipeline
```
API Request (/adk/workflow/invoice/start)
     │
     ▼
┌──────────────────────────┐
│ InvoiceProcessingADKWorkflow │
└──────────────────────────┘
     │
     ├─> 1. ContractProcessingADKAgent: Ingests PDF/text, creates embeddings, and runs RAG to extract initial structured data.
     │
     ├─> 2. ValidationADKAgent: Validates the extracted data against business rules. If validation fails, it can pause the workflow and request human input.
     │
     ├─> 3. CorrectionADKAgent: Applies any human-provided corrections, cleans the data, and generates the final, canonical invoice JSON.
     │
     ├─> 4. InvoiceGeneratorADKAgent: Creates a formal invoice record in the PostgreSQL database from the corrected JSON.
     │
     ├─> 5. UIGenerationADKAgent: Generates a user-friendly HTML/CSS representation of the invoice from a template.
     │
     └─> 6. ScheduleRetrievalADKAgent: Queries Pinecone for scheduling patterns and uses Google Cloud Scheduler to set up recurring invoice jobs.
```

### Human-in-the-Loop
The `ValidationADKAgent` introduces a critical human-in-the-loop checkpoint.
```
Validation Fails ─> Workflow Pauses ─> API returns "human_input_required"
     │
     ├─> Frontend displays validation issues to the user.
     │
     ├─> User submits corrections via API (/adk/workflow/{id}/resume).
     │
     └─> Workflow resumes, starting with the CorrectionADKAgent.
```

## 🗄️ Database Architecture

(No significant changes in the new architecture)

## 🔐 Security Architecture

(No significant changes in the new architecture)

## 📊 Data Flow Architecture

### ADK Contract Processing Flow
```
Frontend Upload → /adk/workflow/invoice/start → ADK Orchestrator → [Agent Workflow] → Final State in DB
```

### Invoice Generation Flow (ADK)
```
User Request → ADK Orchestrator → Contract Processing → Validation → Correction → Invoice Generation → UI Generation → Scheduling
```

---

*This architecture documentation provides a comprehensive overview of the Smart Invoice Scheduler system design, focusing on the new Google ADK-based agentic workflow.*
