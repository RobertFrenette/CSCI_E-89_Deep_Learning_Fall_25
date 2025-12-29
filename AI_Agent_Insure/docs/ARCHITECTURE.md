# Architecture Documentation

Complete architecture overview of the AI Agent Insurance Platform.

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interfaces                           │
├──────────────────────────────┬──────────────────────────────────┤
│   Admin Frontend             │      Client Frontend             │
│   (Next.js 16)              │      (Flask)                      │
│   Port: 3000                │      Port: 5001                   │
│   - Dashboard               │      - Customer Portal            │
│   - Policies Management     │      - Policy View                │
│   - Claims Management       │      - Claims Submission          │
│   - AI Chat                 │      - AI Chat Widget             │
│   - Document Upload         │      - User Profile               │
└──────────────┬──────────────┴──────────────┬───────────────────┘
               │                              │
               ▼                              ▼
┌──────────────────────────────┬──────────────────────────────────┐
│   Admin Backend              │      Client Backend               │
│   (Express/TypeScript)       │      (FastAPI)                   │
│   Port: 3001                │      Port: 8001                   │
│   - REST API                │      - REST API                   │
│   - PostgreSQL Access       │      - PostgreSQL Access          │
│   - Data Refresh            │      - MongoDB Access             │
│   - OpenAPI Docs            │      - JWT Authentication        │
└──────────────┬──────────────┴──────────────┬───────────────────┘
               │                              │
               └──────────────┬───────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   AI Agent API  │
                    │   (FastAPI)     │
                    │   Port: 8002    │
                    │   - Query Router│
                    │   - RAG Engine  │
                    │   - PDF Upload  │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  PostgreSQL   │   │   MongoDB     │   │   ChromaDB    │
│  Port: 5432   │   │   Port: 27017 │   │   Port: 8000  │
│               │   │               │   │               │
│ - insureds    │   │ - user_profiles│   │ - knowledge_  │
│ - policies   │   │ - query_history│   │   base         │
│ - claims     │   │               │   │ - embeddings   │
│ - coverage   │   │               │   │               │
│ - risk_profiles│ │               │   │               │
└───────────────┘   └───────────────┘   └───────┬───────┘
                                                 │
                                                 ▼
                                          ┌───────────────┐
                                          │    Ollama     │
                                          │  Port: 11434  │
                                          │               │
                                          │ - phi3:mini   │
                                          │ - nomic-embed │
                                          └───────────────┘
```

## Data Flow Diagrams

### Query Processing Flow

```
User Query
    │
    ▼
Frontend (Admin/Client)
    │
    ▼
Backend API (Admin/Client)
    │
    ▼
AI Agent API
    │
    ├─► Query Router
    │       │
    │       ├─► SQL Indicators? ──► PostgreSQL Query
    │       ├─► RAG Indicators? ──► ChromaDB Vector Search
    │       ├─► MongoDB Indicators? ──► MongoDB Query
    │       └─► Hybrid? ──► Both SQL + RAG
    │
    ▼
Ollama LLM (phi3:mini)
    │
    ▼
Response Generation
    │
    ├─► Stream to Frontend (SSE)
    └─► Log to MongoDB (if authenticated)
```

### Authentication Flow

```
User Registration/Login
    │
    ▼
Client Backend
    │
    ├─► Validate against PostgreSQL (email + policy_number)
    │
    ├─► Create/Update MongoDB user profile
    │
    └─► Generate JWT Token
        │
        ▼
    Return Token to Frontend
        │
        ▼
    Store in Session/Cookie
        │
        ▼
    Include in API Requests (Authorization Header)
```

### PDF Upload Flow

```
PDF File Upload
    │
    ▼
Admin Frontend (/documents)
    │
    ▼
AI Agent API (/api/agent/upload/pdf)
    │
    ├─► Extract Text (pypdf)
    │
    ├─► Chunk Text (1000 chars, 200 overlap)
    │
    ├─► Generate Embeddings (ChromaDB)
    │
    └─► Store in ChromaDB Collection
        │
        ▼
    Return Chunk Count
```

## Component Architecture

### Admin Application

```
admin-app/
├── backend/
│   ├── src/
│   │   ├── routes/
│   │   │   ├── policies.ts      # Policy management
│   │   │   ├── customers.ts     # Customer management
│   │   │   ├── claims.ts        # Claims management
│   │   │   ├── stats.ts         # Statistics
│   │   │   └── data.ts         # Data refresh
│   │   ├── config/
│   │   │   ├── database.ts      # PostgreSQL connection
│   │   │   └── swagger.ts       # OpenAPI spec
│   │   └── types/
│   │       └── index.ts         # TypeScript types
│   └── tests/                   # Unit & integration tests
│
└── frontend/
    ├── src/
    │   ├── app/                 # Next.js pages
    │   │   ├── page.tsx         # Dashboard
    │   │   ├── policies/
    │   │   ├── customers/
    │   │   ├── claims/
    │   │   ├── chat/
    │   │   └── documents/       # PDF upload
    │   ├── components/          # React components
    │   └── lib/
    │       ├── api.ts          # Admin backend client
    │       └── ai-agent-client.ts  # AI agent client
    └── tests/                  # Component tests
```

### Client Application

```
client-app/
├── backend/
│   ├── app/
│   │   ├── routes/
│   │   │   ├── auth.py         # Registration/Login
│   │   │   └── user.py         # User & policy endpoints
│   │   ├── auth.py              # JWT authentication
│   │   ├── database/           # PostgreSQL & MongoDB
│   │   └── models.py           # Pydantic models
│   └── tests/                  # Unit & integration tests
│
└── frontend/
    ├── templates/              # Jinja2 templates
    │   ├── base.html
    │   ├── dashboard.html
    │   ├── chat_widget.html    # Floating chat widget
    │   └── ...
    ├── static/                 # CSS, JS, images
    └── app.py                  # Flask application
```

### AI Agent

```
ai-agent/
├── app/
│   ├── routes/
│   │   └── agent.py            # API endpoints
│   ├── services/
│   │   ├── query_service.py    # Query orchestration
│   │   ├── postgres_service.py # PostgreSQL operations
│   │   ├── mongodb_service.py  # MongoDB operations
│   │   ├── pdf_service.py     # PDF processing
│   │   └── cache_service.py   # Query caching
│   ├── routing/
│   │   ├── query_router.py     # Intelligent routing
│   │   ├── sql_query_handler.py
│   │   ├── mongo_query_handler.py
│   │   └── constants.py       # Routing indicators
│   └── database/              # Connection management
│
└── src/
    ├── rag_engine.py          # RAG pipeline
    ├── vector_search.py       # ChromaDB search
    ├── ollama_client.py       # LLM client
    └── chromadb_client.py     # Vector store client
```

## Database Schema

### PostgreSQL Schema

```
insureds
├── insured_id (PK)
├── first_name, last_name
├── email_address (UNIQUE)
├── company_name, industry
└── address fields

policies
├── policy_number (PK)
├── insured_id (FK → insureds)
├── policy_type
├── effective_date, expiration_date
├── policy_status
└── annual_premium

coverage_details
├── policy_number (PK, FK → policies)
├── coverage_limit, deductible
├── coverage_tier
└── addon flags

ai_risk_profile
├── policy_number (PK, FK → policies)
├── ai_system_type
├── risk_score_internal (0-100)
└── deployment details

claims_history
├── claim_id (PK)
├── policy_number (FK → policies)
├── insured_id (FK → insureds)
├── claim_date, claim_type
├── claim_status
└── claim_amount, amount_paid
```

### MongoDB Schema

```
user_profiles
├── _id (ObjectId)
├── username (UNIQUE)
├── email (UNIQUE)
├── password (bcrypt hashed)
├── insured_id
├── policy_number
├── created_at, updated_at
└── last_login

query_history
├── _id (ObjectId)
├── user_id (ObjectId → user_profiles)
├── query_text
├── query_type (sql, rag, hybrid, mongo)
├── answer
├── sources (array)
├── query_timestamp
└── satisfaction_rating (optional)
```

### ChromaDB Collections

```
knowledge_base (default collection)
├── Documents: PDF text chunks
├── Embeddings: Vector embeddings
└── Metadata:
    ├── source (PDF filename)
    ├── source_name
    ├── chunk_index
    └── uploaded (boolean)
```

## Query Routing Logic

### Routing Decision Tree

```
User Query
    │
    ▼
Analyze Keywords & Patterns
    │
    ├─► Strong SQL Indicators?
    │   ├─► Yes ──► Check Access Control
    │   │   ├─► Admin? ──► SQL Query
    │   │   ├─► Authenticated Client? ──► SQL Query (filtered by policy)
    │   │   └─► Guest? ──► Access Denied → RAG
    │   │
    │   └─► No ──► Continue
    │
    ├─► Strong RAG Indicators?
    │   ├─► Yes ──► RAG Query
    │   └─► No ──► Continue
    │
    ├─► MongoDB Indicators?
    │   ├─► Yes ──► MongoDB Query (admin only)
    │   └─► No ──► Continue
    │
    └─► Both SQL & RAG Indicators?
        ├─► Yes ──► Hybrid Query
        └─► No ──► Default to RAG
```

### Routing Indicators

**SQL Indicators:**
- Strong: "insured", "policy", "claim", "customer", "how many", "count"
- Medium: "premium", "deductible", "coverage", "risk score"

**RAG Indicators:**
- Procedures: "how to", "how do i", "steps to", "procedure for"
- Company Info: "company", "about", "what is", "information"
- Products: "product", "coverage", "insurance type"

**MongoDB Indicators:**
- User Profiles: "user profile", "account", "my information"

## Service Dependencies

### Startup Order

1. **Databases** (PostgreSQL, MongoDB, ChromaDB)
2. **Ollama** (LLM service)
3. **Backend Services** (Admin Backend, Client Backend)
4. **AI Agent** (depends on all databases and Ollama)
5. **Frontend Services** (Admin Frontend, Client Frontend)
6. **Dashboard** (depends on all services)

### Health Checks

All services implement health checks:
- **Liveness**: Service is running
- **Readiness**: Service can serve requests (database connected)

## Network Architecture

### Docker Network

```
insure-network (bridge network)
├── postgres (internal)
├── mongodb (internal)
├── chromadb (internal)
├── ollama (internal)
├── admin-backend (internal + exposed:3001)
├── admin-frontend (internal + exposed:3000)
├── client-backend (internal + exposed:8001)
├── client-frontend (internal + exposed:5001)
├── ai-agent (internal + exposed:8002)
└── insure-dashboard (internal + exposed:8501)
```

### Port Mapping

| Service | Internal Port | External Port | Access |
|---------|--------------|---------------|--------|
| Admin Frontend | 3000 | 3000 | [http://localhost:3000](http://localhost:3000) |
| Admin Backend | 3001 | 3001 | [http://localhost:3001](http://localhost:3001) |
| Client Frontend | 5000 | 5001 | [http://localhost:5001](http://localhost:5001) |
| Client Backend | 8001 | 8001 | [http://localhost:8001](http://localhost:8001) |
| AI Agent | 8002 | 8002 | [http://localhost:8002](http://localhost:8002) |
| PostgreSQL | 5432 | 5432 | localhost:5432 |
| MongoDB | 27017 | 27017 | localhost:27017 |
| ChromaDB | 8000 | 8000 | [http://localhost:8000](http://localhost:8000) |
| Ollama | 11434 | 11434 | [http://localhost:11434](http://localhost:11434) |
| Dashboard | 8501 | 8501 | [http://localhost:8501](http://localhost:8501) |

## Security Architecture

### Authentication & Authorization

```
┌─────────────────────────────────────────┐
│         Access Control Matrix            │
├──────────────┬──────────┬───────────────┤
│ Data Source  │  Admin   │ Client/Guest │
├──────────────┼──────────┼───────────────┤
│ PostgreSQL   │   ✅ All │ ✅ Own Policy │
│ MongoDB      │   ✅ All │     ❌ None   │
│ ChromaDB     │   ✅ All │     ✅ All    │
│ Hybrid       │   ✅ All │     ❌ None   │
└──────────────┴──────────┴───────────────┘
```

### Security Layers

1. **Network**: Docker internal network for service communication
2. **Authentication**: JWT tokens for client users
3. **Authorization**: Role-based access control (admin/client/guest)
4. **Data Filtering**: Policy-based filtering for client users
5. **Input Validation**: Pydantic models and TypeScript types

## Performance Optimizations

### Caching Strategy

```
Query Request
    │
    ├─► Check Cache (TTL: 5 minutes)
    │   ├─► Hit? ──► Return Cached Result
    │   └─► Miss? ──► Continue
    │
    ▼
Execute Query
    │
    ▼
Store in Cache (if non-user-specific)
    │
    ▼
Return Result
```

### Connection Pooling

- **PostgreSQL**: 20 max connections, 2 min connections
- **MongoDB**: 50 max connections, 5 min connections
- **Connection Timeouts**: 10s (PostgreSQL), 5s (MongoDB server selection)

## Deployment Architecture

### Container Orchestration

```
docker-compose.yml
├── Services (10 containers)
├── Volumes (4 persistent volumes)
├── Networks (1 bridge network)
└── Health Checks (all services)
```

### Volume Management

- `postgres-data`: PostgreSQL data persistence
- `mongo-data`: MongoDB data persistence
- `chromadb-data`: ChromaDB vector store persistence
- `ollama-models`: Ollama model storage

## Monitoring & Observability

### Health Endpoints

All services expose health endpoints:
- `/health` - Liveness check
- `/health/ready` - Readiness check (where applicable)

### Logging

- **Frontend**: Browser console logs
- **Backend**: Structured logging (Python logging, Morgan for Express)
- **AI Agent**: Detailed query routing and processing logs

### Dashboard

Streamlit dashboard ([http://localhost:8501](http://localhost:8501)) provides:
- Service health monitoring
- Database statistics
- System overview
- Deployment logs

---

## Next Steps

- See [Deployment Guide](DEPLOYMENT.md) for deployment instructions
- See [API Documentation](API_DOCUMENTATION.md) for API details
- See [Environment Setup](ENVIRONMENT_SETUP.md) for configuration

