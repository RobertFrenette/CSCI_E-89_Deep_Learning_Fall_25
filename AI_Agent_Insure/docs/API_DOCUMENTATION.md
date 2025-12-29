# API Documentation

Complete API reference for all services in the AI Agent Insurance Platform.

## Table of Contents

- [Admin Backend API](#admin-backend-api)
- [Client Backend API](#client-backend-api)
- [AI Agent API](#ai-agent-api)

---

## Admin Backend API

**Base URL**: [http://localhost:3001](http://localhost:3001)  
**Documentation**: [http://localhost:3001/docs](http://localhost:3001/docs)  
**OpenAPI Spec**: [http://localhost:3001/docs.json](http://localhost:3001/docs.json)

### Health Endpoints

#### GET /health
Liveness check endpoint.

**Response:**
```json
{
  "success": true,
  "message": "Admin backend is running",
  "timestamp": "2025-12-26T18:00:00.000Z"
}
```

#### GET /health/ready
Readiness check endpoint (verifies database connectivity).

**Response:**
```json
{
  "success": true,
  "message": "Admin backend is ready",
  "database": "connected"
}
```

### Policies Endpoints

#### GET /api/policies
List all policies.

**Query Parameters:**
- `status` (optional): Filter by policy status (e.g., "Active", "Expired")
- `limit` (optional): Limit number of results
- `offset` (optional): Offset for pagination

**Response:**
```json
{
  "success": true,
  "count": 208,
  "data": [
    {
      "policy_number": "P2FUZC2SC",
      "insured_id": "BQ4DCXWL",
      "policy_type": "Model & Data Security Insurance",
      "effective_date": "2024-01-01",
      "expiration_date": "2025-01-01",
      "policy_status": "Active",
      "annual_premium": "7757.00"
    }
  ]
}
```

#### GET /api/policies/:id
Get policy details.

**Response:**
```json
{
  "success": true,
  "data": {
    "policy_number": "P2FUZC2SC",
    "insured_id": "BQ4DCXWL",
    "policy_type": "Model & Data Security Insurance",
    "effective_date": "2024-01-01",
    "expiration_date": "2025-01-01",
    "policy_status": "Active",
    "annual_premium": "7757.00"
  }
}
```

#### GET /api/policies/:id/claims
Get claims for a specific policy.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "claim_id": "C001",
      "claim_date": "2024-06-15",
      "claim_type": "Data Breach",
      "claim_status": "Active",
      "claim_amount": "50000.00"
    }
  ]
}
```

### Customers Endpoints

#### GET /api/customers
List all customers with policy counts.

**Response:**
```json
{
  "success": true,
  "count": 100,
  "data": [
    {
      "insured_id": "BQ4DCXWL",
      "first_name": "Sophia",
      "last_name": "Brown",
      "email_address": "user5653@example.com",
      "company_name": "RoboCorp",
      "industry": "Transportation",
      "policy_count": 2,
      "total_premium": "15000.00"
    }
  ]
}
```

#### GET /api/customers/:id
Get customer details with all policies.

**Response:**
```json
{
  "success": true,
  "data": {
    "customer": {
      "insured_id": "BQ4DCXWL",
      "first_name": "Sophia",
      "last_name": "Brown",
      "email_address": "user5653@example.com",
      "company_name": "RoboCorp"
    },
    "policies": [...]
  }
}
```

#### GET /api/customers/:id/claims
Get all claims for a customer.

**Response:**
```json
{
  "success": true,
  "data": [...]
}
```

### Claims Endpoints

#### GET /api/claims
List all claims with optional status filter.

**Query Parameters:**
- `status` (optional): Filter by claim status (e.g., "Active", "Closed")

**Response:**
```json
{
  "success": true,
  "count": 46,
  "data": [
    {
      "claim_id": "C001",
      "policy_number": "P2FUZC2SC",
      "insured_id": "BQ4DCXWL",
      "claim_date": "2024-06-15",
      "claim_type": "Data Breach",
      "claim_status": "Active",
      "claim_amount": "50000.00"
    }
  ]
}
```

#### GET /api/claims/:id
Get claim details.

**Response:**
```json
{
  "success": true,
  "data": {
    "claim_id": "C001",
    "policy_number": "P2FUZC2SC",
    "claim_date": "2024-06-15",
    "claim_type": "Data Breach",
    "claim_status": "Active",
    "claim_amount": "50000.00",
    "amount_paid": "25000.00"
  }
}
```

#### GET /api/claims/stats/summary
Get claims statistics.

**Response:**
```json
{
  "success": true,
  "data": {
    "total_claims": 46,
    "active_claims": 12,
    "closed_claims": 34,
    "total_claim_amount": "1250000.00",
    "total_amount_paid": "850000.00",
    "avg_claim_amount": "27173.91"
  }
}
```

### Statistics Endpoints

#### GET /api/stats/dashboard
Get comprehensive dashboard statistics.

**Response:**
```json
{
  "success": true,
  "data": {
    "overview": {
      "total_customers": "100",
      "total_policies": "208",
      "active_policies": "195",
      "total_claims": "46",
      "active_claims": "12",
      "total_premium_value": "2450000.00"
    },
    "policyByType": [...],
    "aiSystemTypes": [...],
    "recentClaims": [...]
  }
}
```

#### GET /api/stats/risk-analysis
Get risk analysis data.

**Response:**
```json
{
  "success": true,
  "data": {
    "high_risk_count": 15,
    "medium_risk_count": 120,
    "low_risk_count": 73,
    "avg_risk_score": 45.2
  }
}
```

### Data Management Endpoints

#### POST /api/data/refresh
Refresh PostgreSQL data from CSV files.

**Response:**
```json
{
  "success": true,
  "message": "Data refresh completed successfully",
  "data": {
    "message": "PostgreSQL data has been refreshed from CSV files"
  }
}
```

**Note**: Requires Python 3 in the container or use `./refresh_db.sh` script.

---

## Client Backend API

**Base URL**: [http://localhost:8001](http://localhost:8001)  
**Documentation**: [http://localhost:8001/docs](http://localhost:8001/docs)  
**OpenAPI Spec**: [http://localhost:8001/docs.json](http://localhost:8001/docs.json)

### Health Endpoints

#### GET /health
Liveness check.

**Response:**
```json
{
  "status": "healthy"
}
```

#### GET /health/ready
Readiness check (verifies database connectivity).

**Response:**
```json
{
  "status": "ready",
  "postgres": true,
  "mongodb": true
}
```

### Authentication Endpoints

#### POST /api/auth/register
Register a new user.

**Request Body:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "securepassword123",
  "policy_number": "P2FUZC2SC"
}
```

**Response:**
```json
{
  "_id": "507f1f77bcf86cd799439011",
  "username": "johndoe",
  "email": "john@example.com",
  "insured_id": "BQ4DCXWL",
  "policy_number": "P2FUZC2SC",
  "created_at": "2025-12-26T18:00:00.000Z"
}
```

**Validation:**
- Email and policy_number must match records in PostgreSQL
- Username and email must be unique

#### POST /api/auth/login
Login and get JWT token.

**Request Body** (form-data):
```
username: johndoe
password: securepassword123
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Usage:**
Include token in Authorization header: `Authorization: Bearer <token>`

### User Endpoints

All user endpoints require authentication (JWT token).

#### GET /api/user/me
Get current user's profile.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "_id": "507f1f77bcf86cd799439011",
  "username": "johndoe",
  "email": "john@example.com",
  "insured_id": "BQ4DCXWL",
  "policy_number": "P2FUZC2SC"
}
```

#### GET /api/user/policies
Get all policies for the current user.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "policy_number": "P2FUZC2SC",
    "insured_id": "BQ4DCXWL",
    "policy_type": "Model & Data Security Insurance",
    "effective_date": "2024-01-01",
    "expiration_date": "2025-01-01",
    "premium_amount": "7757.00",
    "status": "Active"
  }
]
```

#### GET /api/user/policies/{policy_number}
Get detailed policy information with coverage.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "policy_number": "P2FUZC2SC",
  "insured_id": "BQ4DCXWL",
  "policy_type": "Model & Data Security Insurance",
  "effective_date": "2024-01-01",
  "expiration_date": "2025-01-01",
  "premium_amount": "7757.00",
  "status": "Active",
  "coverage_details": [
    {
      "coverage_type": "Enhanced",
      "coverage_limit": "1000000.00",
      "deductible": "5000.00",
      "business_interruption_coverage": true,
      "cyber_extension": true,
      "incident_response_addon": true
    }
  ]
}
```

#### GET /api/user/queries
Get user's query history.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `limit` (optional): Number of queries to return (default: 20)

**Response:**
```json
[
  {
    "query_id": "507f1f77bcf86cd799439011",
    "query_text": "How many claims do I have?",
    "query_type": "sql",
    "answer": "You have 3 active claims...",
    "sources": ["PostgreSQL Database"],
    "query_timestamp": "2025-12-26T18:00:00.000Z"
  }
]
```

---

## AI Agent API

**Base URL**: [http://localhost:8002](http://localhost:8002)  
**Documentation**: [http://localhost:8002/docs](http://localhost:8002/docs)  
**OpenAPI Spec**: [http://localhost:8002/docs.json](http://localhost:8002/docs.json)

### Health Endpoint

#### GET /health
Health check with dependency status.

**Response:**
```json
{
  "status": "healthy",
  "chromadb": true,
  "ollama": true,
  "mongodb": true,
  "postgres": true
}
```

**Status Values:**
- `healthy`: All critical services are operational
- `degraded`: Some services are unavailable (e.g., PostgreSQL)

### Chat Endpoints

#### POST /api/agent/chat/stream
Streaming chat interface with intelligent query routing.

**Request Body:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "How many claims are there?"
    }
  ],
  "user_id": "admin",
  "policy_number": null,
  "top_k": 3,
  "temperature": 0.1,
  "collection_name": "knowledge_base"
}
```

**Response:** Server-Sent Events (SSE) stream

**Stream Format:**
```
data: {"chunk": "There are", "query_type": "sql"}

data: {"chunk": " 46 total", "query_type": "sql"}

data: {"chunk": " claims", "query_type": "sql"}

data: {"done": true, "sources": ["PostgreSQL Database"], "query_type": "sql"}
```

**Query Routing:**
- **SQL**: Structured data queries (insureds, policies, claims, statistics)
- **RAG**: Document-based queries (company info, products, procedures)
- **Hybrid**: Combines SQL and RAG for comprehensive answers
- **MongoDB**: User profile queries

**Access Control:**
- `user_id: "admin"`: Full access to all data sources
- Authenticated clients: Access to their own policy data + RAG
- `user_id: "guest"` or null: RAG-only access

**Parameters:**
- `messages` (required): Conversation history
- `user_id` (optional): User ID for logging and context
- `policy_number` (optional): Policy number for authenticated users
- `top_k` (optional): Number of documents to retrieve (default: 3)
- `temperature` (optional): LLM temperature (default: 0.1)
- `collection_name` (optional): ChromaDB collection (default: "knowledge_base")

### History Endpoints

#### GET /api/agent/history/{user_id}
Get query history for a user.

**Query Parameters:**
- `limit` (optional): Number of queries to return (default: 20)

**Response:**
```json
[
  {
    "query_id": "507f1f77bcf86cd799439011",
    "query_text": "How many claims are there?",
    "query_type": "sql",
    "answer": "There are 46 total claims...",
    "sources": ["PostgreSQL Database"],
    "query_timestamp": "2025-12-26T18:00:00.000Z",
    "satisfaction_rating": null
  }
]
```

### Document Management Endpoints

#### POST /api/agent/upload/pdf
Upload and ingest a PDF file into ChromaDB.

**Request:** multipart/form-data

**Form Fields:**
- `file` (required): PDF file
- `collection_name` (optional): ChromaDB collection name (default: "knowledge_base")

**Response:**
```json
{
  "success": true,
  "filename": "document.pdf",
  "chunks_ingested": 45,
  "collection": "knowledge_base",
  "message": "Successfully ingested 45 chunks from document.pdf"
}
```

**Example (cURL):**
```bash
curl -X POST "http://localhost:8002/api/agent/upload/pdf" \
  -F "file=@document.pdf" \
  -F "collection_name=knowledge_base"
```

---

## Authentication

### JWT Token Usage

1. **Login** to get a token:
   ```bash
   curl -X POST "http://localhost:8001/api/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=johndoe&password=password123"
   ```

2. **Use token** in subsequent requests:
   ```bash
   curl -X GET "http://localhost:8001/api/user/me" \
     -H "Authorization: Bearer <your-token>"
   ```

### Token Expiration

- Default expiration: 30 minutes
- Configured in `client-app/backend/app/config.py`

---

## Error Responses

All APIs return consistent error responses:

```json
{
  "success": false,
  "message": "Error description",
  "error": "Detailed error message"
}
```

**HTTP Status Codes:**
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `404`: Not Found
- `500`: Internal Server Error

---

## Rate Limiting

Currently, no rate limiting is implemented. Consider adding rate limiting for production deployments.

---

## API Versioning

All APIs are currently at version 1.0. Future versions will be indicated in the URL path (e.g., `/api/v2/...`).

---

## Interactive Documentation

All APIs provide interactive Swagger/OpenAPI documentation:

- **Admin Backend**: [http://localhost:3001/docs](http://localhost:3001/docs)
- **Client Backend**: [http://localhost:8001/docs](http://localhost:8001/docs)
- **AI Agent**: [http://localhost:8002/docs](http://localhost:8002/docs)

You can test endpoints directly from these documentation pages.

