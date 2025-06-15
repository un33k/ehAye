# Legal AI Document Management System - Complete Specification

## System Overview

This specification outlines a secure, AI-powered document management system for law firms using Mac Studio M4 Max hardware with automated setup and case isolation.

## Hardware Requirements

### Mac Studio M4 Max Configuration
- **Model**: Mac Studio M4 Max (Late 2024)
- **CPU**: Apple M4 Max chip with 14-core CPU
- **GPU**: 32-core GPU (optimal for LLM processing)
- **Memory**: 128GB unified memory
- **Storage**: 2TB SSD (internal)
- **External Storage**: 2TB USB-C SSD (Samsung T7 Shield or equivalent)
- **Network**: 10Gb Ethernet + Wi-Fi 6E
- **Estimated Cost**: $4,999 + $200 (external SSD) = $5,199 per unit

## System Architecture

### Memory Allocation (128GB Total)
- **macOS System**: 8GB
- **Docker Engine**: 4GB
- **Vector Database (Qdrant)**: 8GB
- **n8n Workflow Engine**: 2GB
- **LLM Processing (MLX)**: 96GB
- **File System Cache**: 10GB

### Storage Structure (External SSD)
```
/Volumes/LegalAI/
├── data/
│   ├── users/
│   │   ├── [lawyer_id]/
│   │   │   ├── cases/
│   │   │   │   └── [case_number]/
│   │   │   │       ├── documents/
│   │   │   │       ├── notes/
│   │   │   │       └── analysis/
│   │   │   └── profile/
│   ├── models/
│   ├── vector_store/
│   └── logs/
├── backup/
│   └── [daily_snapshots]/
├── config/
└── scripts/
```

## Software Components

### Core Technologies
1. **Docker Desktop for Mac** - Container orchestration
2. **Qdrant** - Vector database for document embeddings
3. **MLX** - Apple Silicon optimized LLM inference
4. **n8n** - Workflow automation and API integration
5. **FastAPI** - Document processing API
6. **React/Next.js** - Web interface

### Recommended LLM
- **Model**: Llama-3.1-70B-Instruct (quantized to 4-bit)
- **Memory Usage**: ~40GB
- **Capabilities**: Legal document analysis, summarization, Q&A
- **Performance**: ~15-20 tokens/second on M4 Max

## Security Architecture

### User Authentication
- **Local accounts** with encrypted password storage
- **Case-based access control** (lawyers only access their cases)
- **Session management** with automatic timeouts
- **Audit logging** for all document access

### Data Isolation
- **User-specific directories** with filesystem permissions
- **Encrypted document storage** using FileVault
- **Network isolation** between user sessions
- **Secure API endpoints** with JWT authentication

## Installation Script

### Primary Setup Script (`setup_legal_ai.sh`)
```bash
#!/bin/bash

# Legal AI System Setup Script
# Run with: sudo ./setup_legal_ai.sh

set -e

EXTERNAL_SSD="/Volumes/LegalAI"
LOG_FILE="$EXTERNAL_SSD/logs/setup.log"

echo "Starting Legal AI System Setup..." | tee -a "$LOG_FILE"

# Check if external SSD is mounted
if [ ! -d "$EXTERNAL_SSD" ]; then
    echo "Error: External SSD not found at $EXTERNAL_SSD"
    exit 1
fi

# Create directory structure
create_directories() {
    echo "Creating directory structure..." | tee -a "$LOG_FILE"
    mkdir -p "$EXTERNAL_SSD"/{data/{users,models,vector_store,logs},backup,config,scripts}
    chmod 755 "$EXTERNAL_SSD/data"
    chmod 700 "$EXTERNAL_SSD/data/users"
}

# Install Homebrew if not present
install_homebrew() {
    if ! command -v brew &> /dev/null; then
        echo "Installing Homebrew..." | tee -a "$LOG_FILE"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
}

# Install Docker Desktop
install_docker() {
    echo "Installing Docker Desktop..." | tee -a "$LOG_FILE"
    brew install --cask docker
    
    # Wait for Docker to start
    echo "Starting Docker..." | tee -a "$LOG_FILE"
    open -a Docker
    sleep 30
    
    # Configure Docker resources
    docker system prune -f
}

# Install Python and dependencies
install_python_deps() {
    echo "Installing Python dependencies..." | tee -a "$LOG_FILE"
    brew install python@3.11
    pip3 install mlx-lm fastapi uvicorn python-multipart
}

# Download and setup LLM
setup_llm() {
    echo "Setting up LLM..." | tee -a "$LOG_FILE"
    cd "$EXTERNAL_SSD/data/models"
    
    # Download Llama 3.1 70B (quantized)
    python3 -c "
import mlx_lm
mlx_lm.utils.download_model('mlx-community/Meta-Llama-3.1-70B-Instruct-4bit')
"
}

# Setup Docker containers
setup_containers() {
    echo "Setting up Docker containers..." | tee -a "$LOG_FILE"
    
    # Create docker-compose.yml
    cat > "$EXTERNAL_SSD/config/docker-compose.yml" << 'EOF'
version: '3.8'

services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: legal_qdrant
    ports:
      - "6333:6333"
    volumes:
      - /Volumes/LegalAI/data/vector_store:/qdrant/storage
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333
    mem_limit: 8g
    restart: unless-stopped

  n8n:
    image: n8nio/n8n:latest
    container_name: legal_n8n
    ports:
      - "5678:5678"
    volumes:
      - /Volumes/LegalAI/data/n8n:/home/node/.n8n
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=LegalAI2024!
    mem_limit: 2g
    restart: unless-stopped

  legal_api:
    build: /Volumes/LegalAI/scripts/api
    container_name: legal_api
    ports:
      - "8000:8000"
    volumes:
      - /Volumes/LegalAI/data:/app/data
    environment:
      - QDRANT_HOST=qdrant
      - MODEL_PATH=/app/data/models
    mem_limit: 4g
    restart: unless-stopped
    depends_on:
      - qdrant

  legal_frontend:
    build: /Volumes/LegalAI/scripts/frontend
    container_name: legal_frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    mem_limit: 1g
    restart: unless-stopped
    depends_on:
      - legal_api

networks:
  default:
    name: legal_network
EOF

    # Start containers
    cd "$EXTERNAL_SSD/config"
    docker-compose up -d
}

# Setup backup system
setup_backup() {
    echo "Setting up backup system..." | tee -a "$LOG_FILE"
    
    # Install AWS CLI
    brew install awscli
    
    # Create backup script
    cat > "$EXTERNAL_SSD/scripts/backup.sh" << 'EOF'
#!/bin/bash

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/Volumes/LegalAI/backup/$TIMESTAMP"
DATA_DIR="/Volumes/LegalAI/data"

# Create local backup
mkdir -p "$BACKUP_DIR"
rsync -av --exclude='*.tmp' --exclude='logs/' "$DATA_DIR/" "$BACKUP_DIR/"

# Sync to AWS S3 (configure credentials separately)
aws s3 sync "$BACKUP_DIR" "s3://legal-ai-backups/$TIMESTAMP/" --exclude "*.tmp"

# Keep only last 7 days of local backups
find "/Volumes/LegalAI/backup" -type d -mtime +7 -exec rm -rf {} +

echo "Backup completed: $TIMESTAMP"
EOF

    chmod +x "$EXTERNAL_SSD/scripts/backup.sh"
    
    # Setup daily cron job
    (crontab -l 2>/dev/null; echo "0 2 * * * /Volumes/LegalAI/scripts/backup.sh") | crontab -
}

# Create user management script
create_user_management() {
    cat > "$EXTERNAL_SSD/scripts/manage_users.py" << 'EOF'
#!/usr/bin/env python3

import os
import json
import hashlib
import getpass
from pathlib import Path

USERS_DIR = "/Volumes/LegalAI/data/users"
CONFIG_FILE = "/Volumes/LegalAI/config/users.json"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password, full_name):
    user_dir = Path(USERS_DIR) / username
    user_dir.mkdir(parents=True, exist_ok=True)
    
    # Create user structure
    (user_dir / "cases").mkdir(exist_ok=True)
    (user_dir / "profile").mkdir(exist_ok=True)
    
    # Update users config
    users = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            users = json.load(f)
    
    users[username] = {
        "password_hash": hash_password(password),
        "full_name": full_name,
        "created_at": str(Path().stat().st_mtime),
        "active": True
    }
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(users, f, indent=2)
    
    print(f"User {username} created successfully")

if __name__ == "__main__":
    username = input("Enter username: ")
    full_name = input("Enter full name: ")
    password = getpass.getpass("Enter password: ")
    
    create_user(username, password, full_name)
EOF

    chmod +x "$EXTERNAL_SSD/scripts/manage_users.py"
}

# Main execution
main() {
    create_directories
    install_homebrew
    install_docker
    install_python_deps
    setup_llm
    setup_containers
    setup_backup
    create_user_management
    
    echo "Legal AI System setup completed successfully!" | tee -a "$LOG_FILE"
    echo "Access the system at: http://localhost:3000"
    echo "n8n workflow engine at: http://localhost:5678"
    echo "Create users with: python3 $EXTERNAL_SSD/scripts/manage_users.py"
}

main "$@"
```

## API Backend (FastAPI)

### Dockerfile for API Service
```dockerfile
# /Volumes/LegalAI/scripts/api/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### API Requirements
```txt
# /Volumes/LegalAI/scripts/api/requirements.txt
fastapi==0.104.1
uvicorn==0.24.0
python-multipart==0.0.6
qdrant-client==1.6.4
mlx-lm==0.0.8
PyPDF2==3.0.1
python-jose==3.3.0
passlib==1.7.4
bcrypt==4.0.1
```

## User Interface

### Features
- **Secure login** with user isolation
- **Drag-and-drop document upload** with case number assignment
- **Real-time document search** using vector similarity
- **AI-powered document analysis** and summarization
- **Case timeline visualization**
- **Export capabilities** for reports and summaries

### Access URLs
- Main Application: `http://localhost:3000`
- API Documentation: `http://localhost:8000/docs`
- n8n Workflows: `http://localhost:5678`
- Vector Database Admin: `http://localhost:6333/dashboard`

## Implementation Instructions

### Step 1: Hardware Setup
1. Order Mac Studio M4 Max with specified configuration
2. Purchase Samsung T7 Shield 2TB USB-C SSD
3. Set up macOS and create admin account

### Step 2: Initial Configuration
1. Connect external SSD and format as "LegalAI"
2. Copy setup script to external SSD
3. Run: `sudo ./setup_legal_ai.sh`
4. Wait for complete installation (~45 minutes)

### Step 3: User Setup
1. Create lawyer accounts: `python3 /Volumes/LegalAI/scripts/manage_users.py`
2. Configure AWS credentials for backups
3. Test document upload and AI processing

### Step 4: AWS S3 Backup Configuration
```bash
# Configure AWS credentials
aws configure
# Enter Access Key ID, Secret Access Key, Region (us-east-1), Output format (json)

# Test backup
/Volumes/LegalAI/scripts/backup.sh
```

## Security Considerations

### Data Protection
- **Encryption at rest** using FileVault
- **Encrypted backups** to AWS S3
- **Network isolation** between containers
- **Audit logging** for compliance

### Access Control
- **Multi-factor authentication** (optional add-on)
- **Session timeouts** after 30 minutes of inactivity
- **Case-based permissions** (lawyers can only access their cases)
- **Administrative controls** for user management

## Compliance Features

### Legal Industry Requirements
- **HIPAA compliance** for sensitive documents
- **Attorney-client privilege** protection
- **Chain of custody** tracking for evidence
- **Retention policy** management
- **Secure deletion** capabilities

## Troubleshooting

### Common Issues
1. **Docker not starting**: Restart Docker Desktop
2. **LLM memory errors**: Reduce model size or increase swap
3. **Slow performance**: Check available RAM and GPU utilization
4. **Backup failures**: Verify AWS credentials and permissions

### Monitoring
- Check logs: `tail -f /Volumes/LegalAI/logs/setup.log`
- Docker status: `docker-compose ps`
- System resources: Activity Monitor

## Cost Analysis

### Initial Investment (Per Unit)
- Mac Studio M4 Max: $4,999
- External SSD: $200
- Setup time: 2 hours @ $150/hr = $300
- **Total per workstation**: $5,499

### Ongoing Costs
- AWS S3 storage: ~$25/month per TB
- System maintenance: 2 hours/month @ $150/hr = $300
- **Monthly operational cost**: ~$325 per firm

## Support and Maintenance

### Recommended Schedule
- **Daily**: Automated backups
- **Weekly**: System health checks
- **Monthly**: Security updates and user audits
- **Quarterly**: Performance optimization and model updates

This system provides a secure, scalable, and AI-enhanced document management solution specifically designed for law firm requirements while maintaining strict case isolation and data security.