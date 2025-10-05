# 🚀 Deployment Guide

Comprehensive guide for deploying the Meeting Intelligence Platform to production.

## Table of Contents

1. [Google Cloud Platform](#google-cloud-platform)
2. [AWS](#amazon-web-services)
3. [Azure](#microsoft-azure)
4. [Docker Deployment](#docker-deployment)
5. [Environment Variables](#environment-variables)
6. [Performance Optimization](#performance-optimization)
7. [Monitoring & Logging](#monitoring--logging)

---

## Google Cloud Platform

### Using Cloud Run (Serverless)

#### Prerequisites
- Google Cloud account
- `gcloud` CLI installed

#### Steps

```bash
# 1. Configure gcloud
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 2. Build and push Docker image
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/meeting-intelligence

# 3. Deploy API to Cloud Run
gcloud run deploy meeting-intelligence-api \
  --image gcr.io/YOUR_PROJECT_ID/meeting-intelligence \
  --platform managed \
  --region us-central1 \
  --memory 8Gi \
  --cpu 4 \
  --timeout 3600 \
  --max-instances 10 \
  --set-env-vars "OPENAI_API_KEY=${OPENAI_API_KEY}" \
  --set-env-vars "HUGGINGFACE_TOKEN=${HUGGINGFACE_TOKEN}" \
  --allow-unauthenticated

# 4. Deploy Frontend
gcloud run deploy meeting-intelligence-frontend \
  --image gcr.io/YOUR_PROJECT_ID/meeting-intelligence:frontend \
  --platform managed \
  --region us-central1 \
  --set-env-vars "API_BASE_URL=https://meeting-intelligence-api-xxx.run.app" \
  --allow-unauthenticated
```

### Using Google Kubernetes Engine (GKE)

```bash
# 1. Create GKE cluster
gcloud container clusters create meeting-intelligence \
  --num-nodes=3 \
  --machine-type=n1-standard-4 \
  --zone=us-central1-a

# 2. Deploy using kubectl
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
```

### Cloud Storage Setup

```bash
# Create bucket for audio files
gsutil mb gs://meeting-intelligence-audio
gsutil lifecycle set lifecycle.json gs://meeting-intelligence-audio
```

---

## Amazon Web Services

### Using AWS Lambda + API Gateway

#### Prerequisites
- AWS account
- AWS CLI installed
- Serverless Framework

```bash
# Install Serverless Framework
npm install -g serverless

# Deploy
serverless deploy --stage production

# Configure API Gateway
aws apigateway create-rest-api --name meeting-intelligence

# Set up S3 for audio storage
aws s3 mb s3://meeting-intelligence-audio
```

### Using AWS ECS (Elastic Container Service)

```bash
# 1. Build and push to ECR
aws ecr create-repository --repository-name meeting-intelligence

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com

# Build and push
docker build -t meeting-intelligence .
docker tag meeting-intelligence:latest YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/meeting-intelligence:latest
docker push YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/meeting-intelligence:latest

# 2. Create ECS cluster
aws ecs create-cluster --cluster-name meeting-intelligence

# 3. Deploy task definition
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json

# 4. Create service
aws ecs create-service \
  --cluster meeting-intelligence \
  --service-name api \
  --task-definition meeting-intelligence \
  --desired-count 2 \
  --launch-type FARGATE
```

---

## Microsoft Azure

### Using Azure Container Apps

```bash
# 1. Login to Azure
az login

# 2. Create resource group
az group create --name meeting-intelligence --location eastus

# 3. Create Container Registry
az acr create --resource-group meeting-intelligence \
  --name meetingintelligence --sku Basic

# 4. Build and push image
az acr build --registry meetingintelligence \
  --image meeting-intelligence:latest .

# 5. Create Container App
az containerapp create \
  --name meeting-intelligence-api \
  --resource-group meeting-intelligence \
  --image meetingintelligence.azurecr.io/meeting-intelligence:latest \
  --target-port 8000 \
  --ingress external \
  --cpu 4 --memory 8Gi \
  --env-vars OPENAI_API_KEY=$OPENAI_API_KEY
```

### Using Azure Kubernetes Service (AKS)

```bash
# 1. Create AKS cluster
az aks create \
  --resource-group meeting-intelligence \
  --name meeting-intelligence-cluster \
  --node-count 3 \
  --node-vm-size Standard_D4s_v3 \
  --enable-addons monitoring

# 2. Get credentials
az aks get-credentials --resource-group meeting-intelligence \
  --name meeting-intelligence-cluster

# 3. Deploy
kubectl apply -f k8s/
```

---

## Docker Deployment

### Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    restart: always
    volumes:
      - redis_data:/data

  api:
    build:
      context: .
      target: api
    restart: always
    environment:
      - REDIS_URL=redis://redis:6379/0
    env_file:
      - .env.production
    depends_on:
      - redis
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '4'
          memory: 8G

  frontend:
    build:
      context: .
      target: frontend
    restart: always
    depends_on:
      - api
    deploy:
      replicas: 2

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - api
      - frontend

volumes:
  redis_data:
```

### Nginx Configuration

Create `nginx.conf`:

```nginx
upstream api_backend {
    least_conn;
    server api:8000;
}

upstream frontend_backend {
    least_conn;
    server frontend:8501;
}

server {
    listen 80;
    server_name your-domain.com;

    location / {
        return 301 https://$server_name$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    location /api/ {
        proxy_pass http://api_backend/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 600s;
    }

    location / {
        proxy_pass http://frontend_backend/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## Environment Variables

### Production Environment File (.env.production)

```env
# API Keys (Use secret management service)
OPENAI_API_KEY=${SECRET_OPENAI_KEY}
GOOGLE_API_KEY=${SECRET_GOOGLE_KEY}
HUGGINGFACE_TOKEN=${SECRET_HF_TOKEN}

# Models (Use smaller models for cost efficiency)
WHISPER_MODEL=medium
DIARIZATION_MODEL=pyannote/speaker-diarization-3.1
EMOTION_MODEL=speechbrain/emotion-recognition-wav2vec2-IEMOCAP

# LLM Configuration
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo-preview
LLM_TEMPERATURE=0.3

# Application Settings
MAX_AUDIO_LENGTH_MINUTES=180
SAMPLE_RATE=16000

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=["https://your-domain.com"]

# Redis
REDIS_URL=redis://redis:6379/0

# Monitoring
WANDB_API_KEY=${SECRET_WANDB_KEY}
WANDB_PROJECT=meeting-intelligence-prod
```

---

## Performance Optimization

### 1. Model Optimization

```python
# Use quantized models for faster inference
WHISPER_MODEL=medium  # Instead of large-v2
compute_type=int8     # Instead of float16
```

### 2. Caching Strategy

```python
# Enable Redis caching for transcriptions
from functools import lru_cache

@lru_cache(maxsize=100)
def get_transcription(audio_hash):
    # Cache transcription results
    pass
```

### 3. Load Balancing

```yaml
# Use multiple replicas
deploy:
  replicas: 5
  update_config:
    parallelism: 2
    delay: 10s
```

### 4. GPU Optimization

```dockerfile
# Use NVIDIA CUDA base image
FROM nvidia/cuda:12.0-runtime-ubuntu22.04

# Install GPU-optimized libraries
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

---

## Monitoring & Logging

### 1. Weights & Biases Integration

Already integrated! Just set your API key:

```env
WANDB_API_KEY=your_key
WANDB_PROJECT=meeting-intelligence-prod
```

### 2. Prometheus + Grafana

```yaml
# docker-compose.monitoring.yml
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

### 3. Logging with ELK Stack

```bash
# Deploy Elasticsearch, Logstash, Kibana
docker-compose -f docker-compose.elk.yml up -d
```

### 4. Health Checks

```python
# Automated health monitoring
import requests

def check_health():
    response = requests.get("https://api.your-domain.com/health")
    if response.status_code != 200:
        send_alert("API is down!")
```

---

## Security Best Practices

1. **Use Secret Management**
   - AWS Secrets Manager
   - Google Secret Manager
   - Azure Key Vault

2. **Enable HTTPS**
   - Use Let's Encrypt for SSL certificates
   - Configure SSL termination at load balancer

3. **API Rate Limiting**
   ```python
   from slowapi import Limiter
   limiter = Limiter(key_func=get_remote_address)
   
   @app.post("/api/v1/analyze")
   @limiter.limit("10/hour")
   async def analyze_meeting(...):
       pass
   ```

4. **Authentication**
   ```python
   from fastapi.security import HTTPBearer
   security = HTTPBearer()
   ```

---

## Cost Optimization

1. **Use Spot Instances** (AWS/GCP)
2. **Auto-scaling** based on demand
3. **Smaller models** for non-critical use cases
4. **Batch processing** for multiple meetings
5. **Cache frequently accessed results**

---

## Backup & Disaster Recovery

```bash
# Automated backups
# Backup ChromaDB
tar -czf chroma_backup_$(date +%Y%m%d).tar.gz data/chroma_db/

# Upload to cloud storage
gsutil cp chroma_backup_*.tar.gz gs://meeting-intelligence-backups/
```

---

## Support & Maintenance

- Monitor logs daily
- Update dependencies monthly
- Test new models quarterly
- Review and optimize costs monthly

---

**Deployment complete! 🎉**

For issues, check logs:
```bash
# Docker logs
docker-compose logs -f api

# Kubernetes logs
kubectl logs -f deployment/meeting-intelligence-api
```

