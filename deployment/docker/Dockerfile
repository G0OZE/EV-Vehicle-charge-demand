# AICTE Project Workflow Tool - Docker Configuration
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 workflow && \
    chown -R workflow:workflow /app

# Copy requirements first for better caching
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs projects temp backups && \
    chown -R workflow:workflow /app

# Switch to non-root user
USER workflow

# Set environment variables
ENV PYTHONPATH=/app
ENV ENVIRONMENT=production

# Expose port (if needed for web interface)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from src.utils.config_validator import validate_configuration; exit(0 if validate_configuration() else 1)"

# Default command
CMD ["python", "-m", "src.cli.workflow_cli", "--help"]