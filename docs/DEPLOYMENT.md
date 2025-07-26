# AICTE Project Workflow Tool - Deployment Guide

This guide provides comprehensive instructions for deploying the AICTE Project Workflow Automation Tool to various environments.

## Table of Contents

- [Overview](#overview)
- [Deployment Types](#deployment-types)
- [Environment Configuration](#environment-configuration)
- [Local Deployment](#local-deployment)
- [Docker Deployment](#docker-deployment)
- [Systemd Service Deployment](#systemd-service-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Configuration Management](#configuration-management)
- [Monitoring and Logging](#monitoring-and-logging)
- [Troubleshooting](#troubleshooting)

## Overview

The AICTE Project Workflow Tool supports multiple deployment strategies to accommodate different use cases:

- **Local**: Development and testing environments
- **Docker**: Containerized deployment for consistency
- **Systemd**: Linux service deployment for production
- **Cloud**: Scalable cloud platform deployment

## Deployment Types

### Quick Deployment

Use the automated deployment script for quick setup:

```bash
# Local development deployment
python scripts/deploy.py development local

# Docker deployment for staging
python scripts/deploy.py staging docker

# Production systemd service
python scripts/deploy.py production systemd

# Cloud deployment (AWS)
python scripts/deploy.py production cloud --provider aws
```

### Manual Deployment

For custom deployments or troubleshooting, follow the manual steps in each section below.

## Environment Configuration

### Configuration Files

The tool uses environment-specific configuration files:

- `config/config.development.json` - Development settings
- `config/config.staging.json` - Staging environment settings
- `config/config.production.json` - Production settings
- `config/config.testing.json` - Testing configuration

### Environment Variables

Key environment variables:

```bash
# Required
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_USERNAME=your_github_username

# Optional
ENVIRONMENT=production
LOG_LEVEL=INFO
MAX_RETRIES=3
TIMEOUT_SECONDS=30
```

### Configuration Validation

Before deployment, validate your configuration:

```bash
python -m src.utils.config_validator config.json
```

## Local Deployment

### Prerequisites

- Python 3.8+
- Git
- 100MB free disk space

### Steps

1. **Clone and setup**:
   ```bash
   git clone https://github.com/your-org/aicte-workflow-tool.git
   cd aicte-workflow-tool
   ```

2. **Create virtual environment** (recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure the application**:
   ```bash
   cp config/config.development.json config.json
   # Edit config.json with your settings
   ```

5. **Deploy**:
   ```bash
   python scripts/deploy.py development local --create-venv
   ```

6. **Test installation**:
   ```bash
   python -m src.cli.workflow_cli --help
   ```

### Launch Scripts

After deployment, use convenient launch scripts:

**Windows**:
```cmd
workflow.bat --help
```

**Linux/macOS**:
```bash
./workflow.sh --help
```

## Docker Deployment

### Prerequisites

- Docker 20.0+
- Docker Compose 1.29+
- 512MB RAM minimum

### Steps

1. **Prepare configuration**:
   ```bash
   cp config/config.production.json config.json
   # Edit config.json with your settings
   ```

2. **Create environment file**:
   ```bash
   cp .env.template .env
   # Edit .env with your GitHub credentials
   ```

3. **Deploy with script**:
   ```bash
   python scripts/deploy.py production docker
   ```

4. **Or deploy manually**:
   ```bash
   # Build image
   docker build -t aicte-workflow-tool:latest -f deployment/docker/Dockerfile .
   
   # Run with docker-compose
   cd deployment/docker
   docker-compose up -d
   ```

### Docker Management

```bash
# Check status
docker ps

# View logs
docker logs aicte-workflow-tool

# Access container
docker exec -it aicte-workflow-tool bash

# Stop services
docker-compose down

# Update deployment
docker-compose pull && docker-compose up -d
```

### Docker Configuration

The Docker deployment includes:

- **Main application container**
- **Redis for caching** (optional)
- **Persistent volumes** for data
- **Health checks**
- **Automatic restart policies**

## Systemd Service Deployment

### Prerequisites

- Linux system with systemd
- Python 3.8+ installed system-wide
- sudo access

### Steps

1. **Prepare the application**:
   ```bash
   # Install to system location
   sudo mkdir -p /opt/aicte-workflow
   sudo cp -r . /opt/aicte-workflow/
   sudo chown -R workflow:workflow /opt/aicte-workflow
   ```

2. **Deploy as service**:
   ```bash
   python scripts/deploy.py production systemd --user workflow
   ```

3. **Or create service manually**:
   ```bash
   # Create service file
   sudo tee /etc/systemd/system/aicte-workflow.service > /dev/null <<EOF
   [Unit]
   Description=AICTE Project Workflow Automation Tool
   After=network.target
   
   [Service]
   Type=simple
   User=workflow
   WorkingDirectory=/opt/aicte-workflow
   Environment=ENVIRONMENT=production
   ExecStart=/usr/bin/python3 -m src.cli.workflow_cli daemon
   Restart=always
   RestartSec=10
   
   [Install]
   WantedBy=multi-user.target
   EOF
   
   # Enable and start service
   sudo systemctl daemon-reload
   sudo systemctl enable aicte-workflow
   sudo systemctl start aicte-workflow
   ```

### Service Management

```bash
# Check status
sudo systemctl status aicte-workflow

# View logs
sudo journalctl -u aicte-workflow -f

# Restart service
sudo systemctl restart aicte-workflow

# Stop service
sudo systemctl stop aicte-workflow

# Disable service
sudo systemctl disable aicte-workflow
```

## Cloud Deployment

### AWS Deployment

#### Prerequisites

- AWS CLI configured
- AWS CDK (optional)
- Appropriate IAM permissions

#### Steps

1. **Prepare deployment configuration**:
   ```bash
   python scripts/deploy.py production cloud --provider aws --region us-east-1
   ```

2. **Manual AWS setup**:
   ```bash
   # Create EC2 instance
   aws ec2 run-instances \
     --image-id ami-0abcdef1234567890 \
     --instance-type t3.micro \
     --key-name your-key-pair \
     --security-group-ids sg-12345678 \
     --subnet-id subnet-12345678
   
   # Deploy application to instance
   scp -r . ec2-user@your-instance-ip:/home/ec2-user/aicte-workflow/
   ssh ec2-user@your-instance-ip
   cd aicte-workflow
   python scripts/deploy.py production local
   ```

#### AWS Services Integration

- **EC2**: Application hosting
- **S3**: File storage and backups
- **CloudWatch**: Logging and monitoring
- **IAM**: Access management
- **VPC**: Network security

### Google Cloud Platform

```bash
# Deploy to GCP (placeholder)
python scripts/deploy.py production cloud --provider gcp --region us-central1
```

### Microsoft Azure

```bash
# Deploy to Azure (placeholder)
python scripts/deploy.py production cloud --provider azure --region eastus
```

## Configuration Management

### Configuration Templates

Generate configuration templates:

```python
from src.utils.config_validator import ConfigSetup

setup = ConfigSetup()
setup.create_config_templates()
setup.create_environment_file()
```

### Configuration Validation

Validate configuration before deployment:

```python
from src.utils.config_validator import validate_configuration

if validate_configuration("config.json"):
    print("Configuration is valid")
else:
    print("Configuration has errors")
```

### Environment-Specific Settings

| Setting | Development | Staging | Production |
|---------|-------------|---------|------------|
| Log Level | DEBUG | INFO | INFO |
| Console Output | Yes | Yes | No |
| File Encryption | No | Yes | Yes |
| Backup Interval | 24h | 12h | 6h |
| Max Retries | 3 | 4 | 5 |
| Concurrent Uploads | 2 | 3 | 5 |

## Monitoring and Logging

### Log Files

- `logs/workflow.log` - Main application log
- `logs/error.log` - Error-specific log
- `logs/debug.log` - Debug information

### Log Analysis

```bash
# View recent logs
tail -f logs/workflow.log

# Search for errors
grep ERROR logs/workflow.log

# Generate log report
python -c "from src.utils.logging_config import LogAnalyzer; print(LogAnalyzer().generate_report())"
```

### Health Checks

```bash
# Application health check
python -m src.cli.workflow_cli validate

# Configuration validation
python -m src.utils.config_validator

# System resource check
python -c "import psutil; print(f'CPU: {psutil.cpu_percent()}%, Memory: {psutil.virtual_memory().percent}%')"
```

### Monitoring Integration

- **Prometheus**: Metrics collection
- **Grafana**: Visualization
- **AlertManager**: Alerting
- **ELK Stack**: Log aggregation

## Troubleshooting

### Common Issues

#### "Configuration validation failed"

**Solution**:
1. Check configuration file syntax
2. Verify GitHub token is valid
3. Ensure all required fields are filled

```bash
python -m src.utils.config_validator config.json
```

#### "Docker container won't start"

**Solution**:
1. Check Docker logs: `docker logs aicte-workflow-tool`
2. Verify environment variables are set
3. Check file permissions

#### "Systemd service fails to start"

**Solution**:
1. Check service logs: `sudo journalctl -u aicte-workflow -f`
2. Verify user permissions
3. Check Python path and dependencies

#### "GitHub API authentication failed"

**Solution**:
1. Verify GitHub token is correct
2. Check token permissions (needs 'repo' scope)
3. Ensure token hasn't expired

### Rollback Procedures

```bash
# Rollback Docker deployment
python scripts/deploy.py production docker --rollback

# Rollback systemd service
python scripts/deploy.py production systemd --rollback

# Manual rollback
sudo systemctl stop aicte-workflow
sudo systemctl disable aicte-workflow
```

### Getting Help

1. **Check logs** for detailed error information
2. **Run diagnostics**: `python -m src.cli.workflow_cli validate`
3. **Verify configuration**: `python -m src.utils.config_validator`
4. **Contact support** with logs and system information

## Security Considerations

### Production Security

- Use encrypted configuration files
- Implement proper file permissions
- Enable audit logging
- Regular security updates
- Network security (firewalls, VPNs)

### Secrets Management

- Store GitHub tokens securely
- Use environment variables for sensitive data
- Implement key rotation
- Monitor access logs

## Performance Optimization

### Resource Requirements

| Environment | CPU | Memory | Storage |
|-------------|-----|--------|---------|
| Development | 1 core | 512MB | 1GB |
| Staging | 1 core | 1GB | 2GB |
| Production | 2+ cores | 2GB+ | 5GB+ |

### Optimization Tips

- Enable caching for better performance
- Adjust concurrent upload limits
- Monitor resource usage
- Implement connection pooling
- Use SSD storage for better I/O

## Maintenance

### Regular Tasks

- **Daily**: Check logs for errors
- **Weekly**: Verify backups
- **Monthly**: Update dependencies
- **Quarterly**: Security audit

### Updates

```bash
# Update application
git pull origin main
python scripts/deploy.py production local --no-install-deps

# Update dependencies
pip install -r requirements.txt --upgrade

# Restart services
sudo systemctl restart aicte-workflow
```

## Support

- **Documentation**: [docs/](../docs/)
- **Issues**: [GitHub Issues](https://github.com/your-org/aicte-workflow-tool/issues)
- **Email**: support@your-org.com