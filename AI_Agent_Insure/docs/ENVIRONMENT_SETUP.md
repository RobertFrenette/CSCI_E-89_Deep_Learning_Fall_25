# Environment Setup Guide

This guide explains how to configure environment variables and set up the AI Agent Insurance Platform.

## Environment Variables

### Required Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# PostgreSQL Configuration
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=insurance_db
POSTGRES_USER=insure_admin
POSTGRES_PASSWORD=insure_secure_pass_2025

# MongoDB Configuration
MONGO_ROOT_USER=mongo_admin
MONGO_ROOT_PASSWORD=mongo_secure_pass_2025
MONGO_INITDB_DATABASE=insurance_users

# ChromaDB Configuration
CHROMADB_HOST=chromadb
CHROMADB_PORT=8000
CHROMADB_USE_HTTP=true

# Ollama Configuration
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=phi3:mini
OLLAMA_EMBED_MODEL=nomic-embed-text

# Admin Backend
ADMIN_BACKEND_PORT=3001
NODE_ENV=production

# Client Backend
CLIENT_BACKEND_PORT=8001
FLASK_SECRET_KEY=your-secret-key-change-in-production

# AI Agent
AI_AGENT_PORT=8002

# Frontend URLs (for client-side API calls)
NEXT_PUBLIC_API_URL=http://localhost:3001
NEXT_PUBLIC_AI_AGENT_URL=http://localhost:8002

# Dashboard
ENVIRONMENT=container
```

### Environment File Template

A complete `.env` template:

```bash
# ============================================
# AI Agent Insurance Platform - Environment
# ============================================

# Database Configuration
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=insurance_db
POSTGRES_USER=insure_admin
POSTGRES_PASSWORD=insure_secure_pass_2025

MONGO_ROOT_USER=mongo_admin
MONGO_ROOT_PASSWORD=mongo_secure_pass_2025
MONGO_INITDB_DATABASE=insurance_users

# Vector Store
CHROMADB_HOST=chromadb
CHROMADB_PORT=8000
CHROMADB_USE_HTTP=true

# LLM Configuration
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=phi3:mini
OLLAMA_EMBED_MODEL=nomic-embed-text

# Service Ports
ADMIN_BACKEND_PORT=3001
CLIENT_BACKEND_PORT=8001
AI_AGENT_PORT=8002

# Security
FLASK_SECRET_KEY=dev-secret-key-change-in-production
NODE_ENV=production

# Frontend Configuration
NEXT_PUBLIC_API_URL=http://localhost:3001
NEXT_PUBLIC_AI_AGENT_URL=http://localhost:8002

# Dashboard
ENVIRONMENT=container
```

## Local Development Setup

### Option 1: Docker Compose (Recommended)

1. **Create `.env` file**
   ```bash
   cp .env.example .env
   # Edit .env with your values
   ```

2. **Deploy services**
   ```bash
   ./deploy.sh
   ```

3. **Verify services are running**
   ```bash
   docker-compose ps
   ```

### Option 2: Local Development (Without Docker)

#### Prerequisites

- Node.js 20+ (for admin-app)
- Python 3.11+ (for client-app and ai-agent)
- PostgreSQL 15+
- MongoDB 7+
- ChromaDB (via Docker or local install)
- Ollama (local install)

#### Setup Steps

1. **Install PostgreSQL**
   ```bash
   # macOS
   brew install postgresql@15
   
   # Linux
   sudo apt-get install postgresql-15
   ```

2. **Install MongoDB**
   ```bash
   # macOS
   brew install mongodb-community@7
   
   # Linux
   sudo apt-get install mongodb
   ```

3. **Install Ollama**
   ```bash
   # macOS/Linux
   curl -fsSL https://ollama.com/install.sh | sh
   ```

4. **Start Services**
   ```bash
   # PostgreSQL
   brew services start postgresql@15  # macOS
   # or
   sudo systemctl start postgresql    # Linux
   
   # MongoDB
   brew services start mongodb-community@7  # macOS
   # or
   sudo systemctl start mongod               # Linux
   
   # Ollama
   ollama serve
   ```

5. **Initialize Databases**
   ```bash
   # PostgreSQL
   psql -U postgres -f database-init/postgres/schema.sql
   cd database-init && python3 load_data.py
   
   # MongoDB
   mongosh < database-init/mongodb/init-mongo.sh
   cd database-init && python3 load_mongo_data.py
   ```

6. **Start Application Services**
   ```bash
   # Admin Backend
   cd admin-app/backend
   npm install
   npm run dev
   
   # Admin Frontend
   cd admin-app/frontend
   npm install
   npm run dev
   
   # Client Backend
   cd client-app/backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8001
   
   # Client Frontend
   cd client-app/frontend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   flask run --port 5001
   
   # AI Agent
   cd ai-agent
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8002
   ```

## Environment Variable Reference

### PostgreSQL Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_HOST` | `postgres` | PostgreSQL host (use `localhost` for local dev) |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
| `POSTGRES_DB` | `insurance_db` | Database name |
| `POSTGRES_USER` | `insure_admin` | Database user |
| `POSTGRES_PASSWORD` | `insure_secure_pass_2025` | Database password |

### MongoDB Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGO_ROOT_USER` | `mongo_admin` | MongoDB root username |
| `MONGO_ROOT_PASSWORD` | `mongo_secure_pass_2025` | MongoDB root password |
| `MONGO_INITDB_DATABASE` | `insurance_users` | Initial database name |

### ChromaDB Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CHROMADB_HOST` | `chromadb` | ChromaDB host (use `localhost` for local dev) |
| `CHROMADB_PORT` | `8000` | ChromaDB port |
| `CHROMADB_USE_HTTP` | `true` | Use HTTP client (vs persistent client) |

### Ollama Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Ollama API base URL |
| `OLLAMA_MODEL` | `phi3:mini` | LLM model name |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Embedding model name |

### Service Ports

| Variable | Default | Description |
|----------|---------|-------------|
| `ADMIN_BACKEND_PORT` | `3001` | Admin backend API port |
| `CLIENT_BACKEND_PORT` | `8001` | Client backend API port |
| `AI_AGENT_PORT` | `8002` | AI agent API port |

### Security Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_SECRET_KEY` | `dev-secret-key...` | Flask session secret (change in production!) |
| `NODE_ENV` | `production` | Node.js environment |

### Frontend Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | [http://localhost:3001](http://localhost:3001) | Admin frontend API URL |
| `NEXT_PUBLIC_AI_AGENT_URL` | [http://localhost:8002](http://localhost:8002) | Admin frontend AI agent URL |

## Production Considerations

### Security Best Practices

1. **Change Default Passwords**
   - Update all database passwords
   - Use strong, unique passwords
   - Store in secure secret management system

2. **Environment Variables**
   - Never commit `.env` files to version control
   - Use environment-specific configuration
   - Rotate secrets regularly

3. **Network Security**
   - Use internal networks for service communication
   - Expose only necessary ports
   - Implement firewall rules

4. **SSL/TLS**
   - Use HTTPS in production
   - Configure SSL certificates
   - Enable secure database connections

### Performance Tuning

1. **Database Connections**
   - Adjust connection pool sizes based on load
   - Monitor connection usage
   - Set appropriate timeouts

2. **Caching**
   - Configure cache TTL based on data freshness requirements
   - Monitor cache hit rates
   - Adjust cache size as needed

3. **Resource Limits**
   - Set Docker container resource limits
   - Monitor memory and CPU usage
   - Scale services horizontally as needed

## Troubleshooting

### Common Issues

1. **Port Conflicts**
   - Check if ports are already in use: `lsof -i :PORT`
   - Change port in `.env` and `docker-compose.yml`

2. **Database Connection Failures**
   - Verify database services are running
   - Check network connectivity
   - Verify credentials in `.env`

3. **Ollama Model Not Found**
   - Pull model: `docker exec insure-ollama ollama pull phi3:mini`
   - Check model name in `.env`

4. **Permission Errors**
   - Check file permissions on data directories
   - Verify Docker volume mounts
   - Check user permissions in containers

## Next Steps

- See [Deployment Guide](DEPLOYMENT.md) for deployment instructions
- See [API Documentation](API_DOCUMENTATION.md) for API details
- See [Architecture](ARCHITECTURE.md) for system architecture

