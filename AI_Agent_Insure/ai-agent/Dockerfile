# Multi-stage build for AI Agent API
FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY src/ ./src/

# Production stage
FROM base as production

# Copy application code
COPY app/ ./app/
COPY src/ ./src/

# Create non-root user
RUN useradd -m -u 1000 aiagent && chown -R aiagent:aiagent /app

# Switch to non-root user
USER aiagent

# Expose port
EXPOSE 8002

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]

