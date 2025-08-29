# Smart Invoice Scheduler - Project Documentation


## 🎥 Demo Resources

### 📹 Video Demo
**Project Demonstration Video**: https://www.loom.com/share/6727f28fbb384bf9987cf88c0b74556d?sid=cc7998e3-e177-40c6-ac81-5bee36001d24
*Comprehensive walkthrough of all features including contract upload, processing, and invoice generation*

### 🎨 System Flow Diagram
**Interactive Flow Diagram**: https://excalidraw.com/
*Visual representation of the contract-to-invoice workflow and system architecture*



## 🚀 Project Overview

Smart Invoice Scheduler is an AI-powered platform that automates contract processing and intelligent invoice generation. The application leverages advanced RAG (Retrieval-Augmented Generation) technology to extract relevant information from rental agreements and service contracts, then automatically generates structured invoice data with intelligent scheduling capabilities.

## 🎯 Key Features

### 🔍 Contract Processing & Analysis
- **PDF Contract Upload**: Support for rental agreements, service contracts, and consulting agreements
- **AI-Powered Text Extraction**: Advanced PDF parsing with OCR capabilities
- **Smart Contract Analysis**: RAG-based contract understanding and information extraction
- **Multi-Party Contract Support**: Handles complex contracts with multiple stakeholders

### 📊 Invoice Generation & Management
- **Automated Invoice Creation**: Generate invoices directly from contract data
- **Template-Based System**: Customizable invoice templates for different contract types
- **Multi-Format Support**: PDF, HTML, and structured data formats
- **Validation & Approval Workflows**: Built-in approval processes with validation rules

### 🗓️ Intelligent Scheduling
- **Calendar Integration**: Visual calendar interface for invoice scheduling
- **Recurring Invoice Setup**: Monthly, quarterly, annual, and custom scheduling
- **Due Date Management**: Automated calculation of payment due dates
- **Reminder System**: Email notifications for upcoming invoices

### 🔐 Enterprise Security & Authentication
- **Role-Based Access Control**: Tenant and rent-payer user roles with specific permissions
- **Multi-Factor Authentication**: Enhanced security with email verification
- **Session Management**: Secure session handling with token-based auth
- **Audit Trail**: Complete security event logging

### 🤖 AI-Powered Features
- **Contract RAG Service**: Natural language queries for contract information
- **Smart Data Extraction**: Automatic identification of parties, payment terms, and services
- **Embedding Generation**: Vector-based document storage for fast retrieval
- **Confidence Scoring**: AI confidence ratings for extracted data accuracy

## 🏗️ System Architecture

### Frontend (React + TypeScript)
- **Framework**: React 19.1.1 with TypeScript
- **Styling**: TailwindCSS 4.1.12 with custom components
- **State Management**: Zustand for global state
- **Routing**: React Router DOM 7.8.2
- **Build Tool**: Vite 7.1.2

### Backend (FastAPI + Python)
- **Framework**: FastAPI with async support
- **Database**: PostgreSQL with SQLAlchemy ORM
- **AI/ML**: Pinecone vector database for embeddings
- **File Storage**: Google Cloud Storage integration
- **Authentication**: JWT-based with bcrypt password hashing

## 📊 Database Schema

### Core Tables

#### Users Table
```sql
CREATE TABLE users (
    id VARCHAR PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    password_hash VARCHAR(255) NOT NULL,
    role user_role NOT NULL, -- 'tenant' | 'rent_payer'
    status user_status NOT NULL DEFAULT 'active',
    tenant_email VARCHAR(255), -- For rent_payers
    address_id VARCHAR REFERENCES addresses(id),
    email_verified BOOLEAN DEFAULT FALSE,
    phone_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### Addresses Table
```sql
CREATE TABLE addresses (
    id VARCHAR PRIMARY KEY DEFAULT uuid_generate_v4(),
    street VARCHAR(255) NOT NULL,
    building_number VARCHAR(20),
    room_number VARCHAR(10),
    floor VARCHAR(10),
    apartment_unit VARCHAR(20),
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    postal_code VARCHAR(20) NOT NULL,
    country VARCHAR(100) DEFAULT 'USA',
    landmark VARCHAR(255),
    neighborhood VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### Security Events Table
```sql
CREATE TABLE security_events (
    id VARCHAR PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(50) NOT NULL,
    user_id VARCHAR REFERENCES users(id),
    email VARCHAR(255),
    ip_address VARCHAR(45),
    user_agent TEXT,
    event_metadata JSON,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);
```

#### User Sessions Table
```sql
CREATE TABLE user_sessions (
    id VARCHAR PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR REFERENCES users(id) NOT NULL,
    session_token VARCHAR(255) NOT NULL UNIQUE,
    ip_address VARCHAR(45),
    user_agent TEXT,
    device_info VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    last_activity TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Enumerations

#### User Roles
- `TENANT`: Property owner with full management access
- `RENT_PAYER`: Tenant with limited payment-focused access

#### User Status
- `ACTIVE`: Normal active user
- `INACTIVE`: Temporarily deactivated
- `SUSPENDED`: Account suspended
- `PENDING_VERIFICATION`: Awaiting email verification

#### Contract Types
- `SERVICE_AGREEMENT`: General service contracts
- `RENTAL_LEASE`: Property rental agreements
- `MAINTENANCE_CONTRACT`: Property maintenance agreements
- `SUPPLY_CONTRACT`: Supply and delivery contracts
- `CONSULTING_AGREEMENT`: Professional consulting contracts
- `OTHER`: Other contract types

#### Invoice Frequencies
- `MONTHLY`: Monthly recurring invoices
- `QUARTERLY`: Quarterly billing cycles
- `BIANNUALLY`: Twice yearly billing
- `ANNUALLY`: Annual billing cycles
- `ONE_TIME`: Single payment contracts
- `CUSTOM`: Custom scheduling patterns

## 🛠️ API Endpoints

### Authentication Endpoints
```http
POST /auth/login
POST /auth/register
POST /auth/logout
POST /auth/refresh-token
POST /auth/verify-email
POST /auth/forgot-password
POST /auth/reset-password
GET  /auth/me
```

### Contract Management Endpoints
```http
POST /contracts/upload-and-process
POST /contracts/generate-invoice-data
POST /contracts/query
POST /contracts/process-and-generate-invoice
GET  /contracts/health
```

### Invoice Management Endpoints
```http
POST /invoices/create_invoice
POST /invoices/approve_invoice
POST /invoices/multi-invoice
POST /invoices/upload-invoice
GET  /invoices/get-all-invoices
GET  /invoices/initial-invoice/{file_name}
POST /invoices/invoice-preview
POST /invoices/invoice-approval
POST /invoices/validate-invoice
POST /invoices/schedule-invoice
GET  /invoices/schedules
GET  /invoices/schedules/{schedule_id}
```

### User Management Endpoints
```http
GET  /users/profile
PUT  /users/profile
GET  /users/permissions
POST /users/change-password
```

### Document Processing Endpoints
```http
POST /documents/upload
GET  /documents/list
GET  /documents/{document_id}
DELETE /documents/{document_id}
```

### AI & Embeddings Endpoints
```http
POST /embeddings/generate
POST /llm/chat
POST /llm/analyze-document
GET  /embeddings/search
```

## 📋 Contract Schema Models

### ContractInvoiceData
```python
class ContractInvoiceData(BaseModel):
    # Contract Information
    contract_title: Optional[str] = None
    contract_type: Optional[ContractType] = None
    contract_number: Optional[str] = None
    
    # Parties
    client: Optional[ContractParty] = None
    service_provider: Optional[ContractParty] = None
    
    # Contract Dates
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    effective_date: Optional[date] = None
    
    # Payment Information
    payment_terms: Optional[PaymentTerms] = None
    services: List[ServiceItem] = []
    
    # Invoice Schedule
    invoice_frequency: Optional[InvoiceFrequency] = None
    first_invoice_date: Optional[date] = None
    next_invoice_date: Optional[date] = None
```

### ContractParty
```python
class ContractParty(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    tax_id: Optional[str] = None
    role: str  # client, service_provider, tenant, landlord
```

### PaymentTerms
```python
class PaymentTerms(BaseModel):
    amount: Optional[Decimal] = None
    currency: str = "USD"
    frequency: Optional[InvoiceFrequency] = None
    due_days: Optional[int] = 30
    late_fee: Optional[Decimal] = None
    discount_terms: Optional[str] = None
```

## 🔒 User Permissions Matrix

### Tenant Role Permissions
```json
{
  "dashboard_access": true,
  "view_all_properties": true,
  "create_rental_agreements": true,
  "edit_rental_agreements": true,
  "delete_rental_agreements": true,
  "manage_rent_payers": true,
  "view_reports": true,
  "export_data": true,
  "send_payment_reminders": true
}
```

### Rent Payer Role Permissions
```json
{
  "dashboard_access": true,
  "view_own_payments": true,
  "view_payment_due": true,
  "make_payments": true,
  "view_payment_receipts": true,
  "view_rental_agreement": true,
  "update_profile": true
}
```



## 🚦 Getting Started

### Prerequisites
- Node.js 18+ for frontend
- Python 3.9+ for backend
- PostgreSQL 13+
- Pinecone API key for vector database
- Google Cloud Storage credentials

### Frontend Setup
```bash
cd client
npm install
npm run dev
```

### Backend Setup
```bash
cd server
pip install -r requirements.txt
python main.py
```

## 🔧 Technology Stack

### Frontend Technologies
- **React 19.1.1**: Modern React with concurrent features
- **TypeScript**: Type-safe development
- **TailwindCSS 4.1.12**: Utility-first CSS framework
- **Zustand 5.0.8**: Lightweight state management
- **React Router DOM 7.8.2**: Client-side routing
- **React Big Calendar 1.19.4**: Calendar component for scheduling
- **Lucide React**: Modern icon library
- **Vite 7.1.2**: Fast build tool and dev server

### Backend Technologies
- **FastAPI**: High-performance async web framework
- **SQLAlchemy**: Python SQL toolkit and ORM
- **PostgreSQL**: Relational database
- **Pinecone**: Vector database for embeddings
- **Google Cloud Storage**: File storage service
- **Pydantic**: Data validation using Python type annotations
- **bcrypt**: Password hashing
- **JWT**: JSON Web Tokens for authentication

### AI & Machine Learning
- **RAG Architecture**: Retrieval-Augmented Generation for contract analysis
- **Vector Embeddings**: Semantic search and document understanding
- **OpenAI GPT Integration**: Natural language processing
- **PDF Processing**: Advanced text extraction and OCR

## 📁 Project Structure

```
smart-invoice-scheduler/
├── client/                          # React frontend
│   ├── src/
│   │   ├── components/             # Reusable UI components
│   │   ├── pages/                  # Page components
│   │   ├── stores/                 # Zustand state stores
│   │   ├── types/                  # TypeScript type definitions
│   │   └── utils/                  # Utility functions
│   ├── api/                        # API client functions
│   └── package.json                # Frontend dependencies
├── server/                          # FastAPI backend
│   ├── models/                     # SQLAlchemy database models
│   ├── routes/                     # API route handlers
│   ├── services/                   # Business logic services
│   ├── schemas/                    # Pydantic schemas
│   ├── middleware/                 # Authentication middleware
│   └── db/                         # Database configuration
└── deliverables/                   # Project documentation
    └── README.md                   # This documentation file
```

## 🎯 Future Enhancements

- **Mobile Application**: React Native mobile app
- **Advanced Analytics**: Business intelligence dashboard
- **Multi-Language Support**: Internationalization
- **API Integrations**: QuickBooks, Stripe, PayPal integration
- **Advanced AI Features**: Predictive analytics for payment patterns
- **Blockchain Integration**: Smart contracts and crypto payments

---

*This documentation provides a comprehensive overview of the Smart Invoice Scheduler platform. For technical support or feature requests, please refer to the project repository or contact the development team.*