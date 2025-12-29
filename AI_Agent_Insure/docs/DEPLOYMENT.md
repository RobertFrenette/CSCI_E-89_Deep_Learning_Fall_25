# Deployment Guide

Complete guide for deploying the AI Agent Insurance Platform.

## Prerequisites

- Docker Desktop (or Docker Engine + Docker Compose)
- 8GB+ RAM available
- 20GB+ free disk space
- macOS, Linux, or Windows with WSL2

## Quick Deployment

### Step 1: Clone and Setup

```bash
git clone <repository-url>
git checkout feature/refactor-ai-agent-insure-platform
cd AI_Agent_Insure
```

### Step 2: Configure Environment

```bash
# Create .env file (see Environment Setup Guide)
cp .env.example .env
# Edit .env with your configuration
```

### Step 3: Deploy

```bash
# Make scripts executable
chmod +x deploy.sh destroy.sh refresh_db.sh

# Deploy all services
./deploy.sh
```

The deployment script will:
1. Create Docker network
2. Build all Docker images
3. Start all services in correct order
4. Run database initialization
5. Run unit and integration tests
6. Display service URLs

### Step 4: Verify Deployment

Check service health:
```bash
# Check all containers
docker-compose ps

# Check logs
docker-compose logs -f

# Or check individual services
curl http://localhost:3001/health  # Admin Backend
curl http://localhost:8001/health  # Client Backend
curl http://localhost:8002/health  # AI Agent
```

## Deployment Process

### Automated Deployment (deploy.sh)

The `deploy.sh` script automates the entire deployment:

1. **Pre-deployment Checks**
   - Verify Docker is running
   - Check Docker network exists
   - Create logs directory

2. **Database Services**
   - Start PostgreSQL
   - Start MongoDB
   - Start ChromaDB
   - Wait for health checks

3. **Ollama Setup**
   - Start Ollama container
   - Pull required models (phi3:mini, nomic-embed-text)
   - Verify model availability

4. **Backend Services**
   - Build and start Admin Backend
   - Build and start Client Backend
   - Wait for health checks

5. **AI Agent**
   - Build and start AI Agent
   - Verify all dependencies

6. **Frontend Services**
   - Build and start Admin Frontend
   - Build and start Client Frontend

7. **Dashboard**
   - Build and start Streamlit Dashboard

8. **Testing**
   - Run unit tests for all services
   - Run integration tests
   - Report test results

9. **Final Status**
   - Display service URLs
   - Show deployment summary


## Service URLs

After deployment, access services at:

| Service | URL | Description |
|---------|-----|-------------|
| Admin Dashboard | [http://localhost:3000](http://localhost:3000) | Admin portal |
| Client Portal | [http://localhost:5001](http://localhost:5001) | Customer portal |
| Systems Dashboard | [http://localhost:8501](http://localhost:8501) | System monitoring |
| Admin API | [http://localhost:3001](http://localhost:3001) | Admin backend API |
| Admin API Docs | [http://localhost:3001/docs](http://localhost:3001/docs) | Swagger UI |
| Client API | [http://localhost:8001](http://localhost:8001) | Client backend API |
| Client API Docs | [http://localhost:8001/docs](http://localhost:8001/docs) | Swagger UI |
| AI Agent API | [http://localhost:8002](http://localhost:8002) | AI agent API |
| AI Agent Docs | [http://localhost:8002/docs](http://localhost:8002/docs) | Swagger UI |

## Database Initialization

### Automatic Initialization

The deployment script automatically:
1. Initializes PostgreSQL schema
2. Loads CSV data into PostgreSQL
3. Initializes MongoDB collections
4. Loads user data into MongoDB
5. Ingests PDF documents into ChromaDB

### Manual Initialization

If you need to reinitialize databases:

```bash
# PostgreSQL
docker exec -it insure-postgres psql -U insure_admin -d insurance_db -f /docker-entrypoint-initdb.d/schema.sql
docker exec -it insure-postgres python3 /database-init/load_data.py

# MongoDB
docker exec -it insure-mongodb mongosh -u mongo_admin -p mongo_secure_pass_2025 --authenticationDatabase admin < database-init/mongodb/init-mongo.sh
docker exec -it insure-mongodb python3 /database-init/load_mongo_data.py

# ChromaDB (PDF ingestion)
docker exec -it insure-ai-agent python3 /database-init/ingest_pdfs.py
```

## Updating Services

### Rebuild and Restart

```bash
# Rebuild specific service
docker-compose build admin-backend
docker-compose up -d admin-backend

# Rebuild all services
docker-compose build
docker-compose up -d
```

### Update Code

```bash
# Pull latest code
git pull

# Rebuild and restart
./deploy.sh
```

## Stopping Services

### Graceful Shutdown

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (⚠️ deletes data)
docker-compose down -v
```

### Using destroy.sh

```bash
# Stop all services and clean up
./destroy.sh
```

This script:
- Stops all containers
- Removes containers
- Removes volumes (optional)
- Cleans up network

## Troubleshooting

### Common Issues

#### 1. Port Already in Use

**Error**: `Bind for 0.0.0.0:3000 failed: port is already allocated`

**Solution**:
```bash
# Find process using port
lsof -i :3000

# Kill process or change port in docker-compose.yml
```

#### 2. Database Connection Failed

**Error**: `Connection refused` or `Connection timeout`

**Solution**:
```bash
# Check database containers are running
docker-compose ps

# Check database logs
docker-compose logs postgres
docker-compose logs mongodb

# Restart databases
docker-compose restart postgres mongodb
```

#### 3. Ollama Model Not Found

**Error**: `Model 'phi3:mini' not found`

**Solution**:
```bash
# Pull model manually
docker exec insure-ollama ollama pull phi3:mini
docker exec insure-ollama ollama pull nomic-embed-text

# Verify models
docker exec insure-ollama ollama list
```

#### 4. Container Exits Immediately

**Error**: Container starts then exits with code 1

**Solution**:
```bash
# Check logs
docker-compose logs <service-name>

# Common causes:
# - Missing environment variables
# - Database not ready
# - Port conflicts
# - Build errors
```

#### 5. Frontend Build Fails

**Error**: Build errors in Next.js or Flask

**Solution**:
```bash
# Clear build cache
docker-compose build --no-cache admin-frontend

# Check Node.js/Python versions
docker-compose exec admin-frontend node --version
```

#### 6. AI Agent Health Check Fails

**Error**: AI Agent shows "degraded" status

**Solution**:
```bash
# Check AI Agent logs
docker-compose logs ai-agent

# Verify dependencies
curl http://localhost:8002/health

# Check individual services
docker-compose logs chromadb
docker-compose logs ollama
docker-compose logs mongodb
```

### Debugging Commands

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f ai-agent

# Execute command in container
docker-compose exec ai-agent bash

# Check container status
docker-compose ps

# Check resource usage
docker stats

# Inspect network
docker network inspect insure-network

# Check volumes
docker volume ls
docker volume inspect insure_postgres-data
```

## Production Deployment

### Security Considerations

1. **Change Default Passwords**
   ```bash
   # Update .env with strong passwords
   POSTGRES_PASSWORD=<strong-password>
   MONGO_ROOT_PASSWORD=<strong-password>
   FLASK_SECRET_KEY=<strong-secret-key>
   ```

2. **Use HTTPS**
   - Configure reverse proxy (nginx/traefik)
   - Use SSL certificates
   - Update frontend URLs to HTTPS

3. **Network Security**
   - Use internal Docker networks
   - Expose only necessary ports
   - Implement firewall rules

4. **Environment Variables**
   - Use secret management (Docker secrets, Vault)
   - Never commit `.env` files
   - Rotate secrets regularly

### Scaling Considerations

1. **Horizontal Scaling**
   - Use Docker Swarm or Kubernetes
   - Scale stateless services (frontends, backends)
   - Use load balancer

2. **Database Scaling**
   - PostgreSQL: Read replicas
   - MongoDB: Replica sets
   - ChromaDB: Multiple instances

3. **Resource Limits**
   ```yaml
   # docker-compose.yml
   services:
     ai-agent:
       deploy:
         resources:
           limits:
             cpus: '2'
             memory: 4G
   ```

### Monitoring

1. **Health Checks**
   - All services have health endpoints
   - Use monitoring tools (Prometheus, Grafana)
   - Set up alerts

2. **Logging**
   - Centralized logging (ELK stack, Loki)
   - Log aggregation
   - Log retention policies

3. **Performance Monitoring**
   - Database query performance
   - API response times
   - Cache hit rates

## Backup and Recovery

### Database Backups

```bash
# PostgreSQL backup
docker exec insure-postgres pg_dump -U insure_admin insurance_db > backup.sql

# MongoDB backup
docker exec insure-mongodb mongodump -u mongo_admin -p mongo_secure_pass_2025 --authenticationDatabase admin --db insurance_users --out /backup

# Restore PostgreSQL
docker exec -i insure-postgres psql -U insure_admin insurance_db < backup.sql

# Restore MongoDB
docker exec insure-mongodb mongorestore -u mongo_admin -p mongo_secure_pass_2025 --authenticationDatabase admin /backup
```

### Volume Backups

```bash
# Backup volumes
docker run --rm -v insure_postgres-data:/data -v $(pwd):/backup alpine tar czf /backup/postgres-backup.tar.gz /data

# Restore volumes
docker run --rm -v insure_postgres-data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres-backup.tar.gz -C /
```

## Rollback Procedure

If deployment fails:

```bash
# Stop all services
docker-compose down

# Restore previous version
git checkout <previous-commit>

# Rebuild and deploy
./deploy.sh
```

## Next Steps

- See [Environment Setup Guide](ENVIRONMENT_SETUP.md) for configuration
- See [API Documentation](API_DOCUMENTATION.md) for API details
- See [Architecture](ARCHITECTURE.md) for system architecture

