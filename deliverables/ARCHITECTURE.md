# System Architecture

## 🏗️ Architecture Overview

Smart Invoice Scheduler follows a modern microservices architecture with clear separation of concerns between the frontend, backend, and AI processing services.

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
│  │  FastAPI    │  │ Middleware  │  │   CORS &    │               │
│  │  Routes     │  │ Auth/Logs   │  │ Validation  │               │
│  └─────────────┘  └─────────────┘  └─────────────┘               │
└─────────────────────────────────────────────────────────────────┘
                                │
                        Service Layer
                                │
┌─────────────────────────────────────────────────────────────────┐
│                        Business Logic Layer                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │
│  │ Contract    │  │  Invoice    │  │    User     │               │
│  │ Processing  │  │ Generation  │  │ Management  │               │
│  └─────────────┘  └─────────────┘  └─────────────┘               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │
│  │  RAG        │  │  Embedding  │  │  Storage    │               │
│  │ Services    │  │  Services   │  │  Services   │               │
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

### State Management Architecture
```typescript
// Zustand Store Structure
interface AppStore {
  auth: AuthState;
  contracts: ContractState;
  invoices: InvoiceState;
}

// Store Composition
const useAuthStore = create<AuthState>(...);
const useContractStore = create<ContractState>(...);
const useInvoiceStore = create<InvoiceState>(...);
```

### Routing Architecture
```typescript
// Protected Route Structure
<Routes>
  <Route path="/auth/*" element={<AuthRoutes />} />
  <Route path="/*" element={
    <ProtectedRoute>
      <AppRoutes />
    </ProtectedRoute>
  } />
</Routes>
```

## 🔧 Backend Architecture

### Service Layer Pattern
```python
# Service Layer Structure
services/
├── contract_processor.py      # Contract PDF processing
├── contract_rag_service.py    # RAG-based analysis
├── contract_db_service.py     # Database operations
├── user_service.py           # User management
├── gcp_storage_service.py    # File storage
└── pinecone_service.py       # Vector operations
```

### API Route Organization
```python
# Route Structure
routes/
├── auth.py          # Authentication endpoints
├── contracts.py     # Contract management
├── invoices.py      # Invoice operations
├── users.py         # User management
├── documents.py     # Document handling
└── embeddings.py    # AI/ML operations
```

### Middleware Stack
```python
# Middleware Chain
Request → CORS → Authentication → Rate Limiting → Route Handler
```

## 🤖 AI Processing Architecture

### RAG (Retrieval-Augmented Generation) Pipeline
```
PDF Upload → Text Extraction → Chunking → Embedding Generation → Vector Storage
                                              ↓
Query Input → Embedding → Vector Search → Context Retrieval → LLM Processing → Response
```

### Contract Processing Flow
```python
class ContractProcessor:
    def process_contract(self, pdf_file, user_id, contract_name):
        # 1. Extract text from PDF
        text = self.extract_pdf_text(pdf_file)
        
        # 2. Clean and preprocess text
        cleaned_text = self.preprocess_text(text)
        
        # 3. Chunk text for embedding
        chunks = self.chunk_text(cleaned_text)
        
        # 4. Generate embeddings
        embeddings = self.generate_embeddings(chunks)
        
        # 5. Store in vector database
        vector_ids = self.store_embeddings(embeddings, metadata)
        
        return ProcessingResult(...)
```

### Invoice Generation Pipeline
```python
class ContractRAGService:
    def generate_invoice_data(self, user_id, contract_name, query):
        # 1. Query vector database for relevant chunks
        relevant_chunks = self.search_similar_chunks(query)
        
        # 2. Build context for LLM
        context = self.build_context(relevant_chunks)
        
        # 3. Generate structured invoice data
        invoice_data = self.llm_extract_invoice_data(context, query)
        
        # 4. Validate and structure response
        return self.validate_invoice_data(invoice_data)
```

## 🗄️ Database Architecture

### Database Design Principles
- **Normalization**: 3NF normalized schema design
- **Indexing**: Strategic indexing for query performance
- **Relationships**: Clear foreign key relationships
- **Constraints**: Data integrity through constraints
- **Audit Trail**: Comprehensive logging and versioning

### Connection Architecture
```python
# Database Connection Management
Database Pool → SQLAlchemy Engine → Session Factory → ORM Models
```

### Migration Strategy
```python
# Alembic Migration Chain
Initial Schema → Migration_001 → Migration_002 → ... → Current Schema
```

## 🔐 Security Architecture

### Authentication Flow
```
Login Request → Credential Validation → JWT Generation → Session Creation → Access Grant
```

### Authorization Model
```python
# Role-Based Access Control (RBAC)
User → Role → Permissions → Resource Access
```

### Security Middleware Stack
```python
# Security Chain
Request → Rate Limiting → Authentication → Authorization → Route Access
```

### Data Protection
- **Encryption at Rest**: Database encryption
- **Encryption in Transit**: HTTPS/TLS
- **Password Security**: bcrypt hashing
- **Token Security**: JWT with expiration
- **Session Management**: Secure session handling

## 📊 Data Flow Architecture

### Contract Upload Flow
```
Frontend Upload → API Gateway → File Validation → Storage Service → Processing Queue → AI Processing → Database Storage
```

### Invoice Generation Flow
```
User Request → Authentication → Contract Retrieval → RAG Processing → Data Extraction → Template Rendering → Response
```

### Real-time Updates
```
Database Change → Event Trigger → WebSocket Notification → Frontend Update
```

## 🚀 Deployment Architecture

### Development Environment
```
Local Dev → Hot Reload → API Server → Local Database
```

### Production Environment
```
Load Balancer → API Gateway → Application Servers → Database Cluster → File Storage
```

### Scalability Considerations
- **Horizontal Scaling**: Multiple API server instances
- **Database Scaling**: Read replicas and connection pooling
- **Caching Strategy**: Redis for session and query caching
- **CDN Integration**: Static asset delivery
- **Microservices Ready**: Service separation for independent scaling

## 🔧 Technology Stack Integration

### Frontend Integration
- **Build Process**: Vite bundling with TypeScript compilation
- **Asset Optimization**: Tree shaking and code splitting
- **Development Tools**: Hot module replacement and debugging

### Backend Integration
- **ASGI Server**: Uvicorn for async request handling
- **Database ORM**: SQLAlchemy with async support
- **API Documentation**: Automatic OpenAPI/Swagger generation
- **Testing Framework**: Pytest with async testing support

### DevOps Integration
- **Containerization**: Docker containers for consistent deployment
- **CI/CD Pipeline**: Automated testing and deployment
- **Monitoring**: Health checks and performance monitoring
- **Logging**: Structured logging with correlation IDs

## 📈 Performance Architecture

### Optimization Strategies
- **Database Indexing**: Query optimization through strategic indexes
- **Connection Pooling**: Efficient database connection management
- **Async Processing**: Non-blocking I/O operations
- **Caching Layers**: Multi-level caching strategy
- **Lazy Loading**: On-demand data loading

### Monitoring and Observability
- **Performance Metrics**: Response time and throughput monitoring
- **Error Tracking**: Comprehensive error logging and alerting
- **Resource Monitoring**: CPU, memory, and database performance
- **User Analytics**: Usage patterns and performance insights

---

*This architecture documentation provides a comprehensive overview of the Smart Invoice Scheduler system design, focusing on scalability, security, and maintainability principles.*