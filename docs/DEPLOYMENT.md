# Deployment Guide

This guide covers deploying the Personal Event Photo Gallery application to production environments.

## Prerequisites

- Docker and Docker Compose
- Domain name (for HTTPS)
- SSL certificates (Let's Encrypt recommended)
- Cloud storage account (AWS S3 or Cloudinary)

## Environment Setup

### 1. Create Environment File

Copy the example environment file and configure it for your environment:

```bash
cp .env.example .env.production
```

Edit `.env.production` with your production values:

```bash
# Database Configuration
POSTGRES_DB=photo_gallery
POSTGRES_USER=gallery_user
POSTGRES_PASSWORD=your_secure_password_here

# Redis Configuration
REDIS_PASSWORD=your_redis_password_here

# Application Security
SECRET_KEY=your_very_long_random_secret_key_here

# Storage Configuration (choose one)
# AWS S3
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-photo-gallery-bucket

# OR Cloudinary
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Frontend Configuration
REACT_APP_API_URL=https://your-domain.com
```

### 2. SSL Certificates

For HTTPS, place your SSL certificates in the `nginx/ssl/` directory:

```bash
mkdir -p nginx/ssl
# Copy your certificates
cp your-cert.pem nginx/ssl/cert.pem
cp your-key.pem nginx/ssl/key.pem
```

For Let's Encrypt certificates:

```bash
# Install certbot
sudo apt-get install certbot

# Get certificates
sudo certbot certonly --standalone -d your-domain.com

# Copy to nginx directory
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/key.pem
```

## Deployment Methods

### Method 1: Automated Deployment Script

Use the provided deployment script:

```bash
# Make script executable
chmod +x scripts/deploy.sh

# Deploy to production
./scripts/deploy.sh production

# Deploy with smoke tests
./scripts/deploy.sh production --test
```

### Method 2: Manual Deployment

1. **Build and start services:**

```bash
# Load environment variables
export $(cat .env.production | grep -v '^#' | xargs)

# Build and start
docker-compose -f docker-compose.prod.yml up -d --build
```

2. **Run database migrations:**

```bash
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

3. **Verify deployment:**

```bash
docker-compose -f docker-compose.prod.yml ps
```

## Cloud Platform Deployment

### AWS Deployment

#### Using AWS ECS

1. **Create ECS cluster:**

```bash
aws ecs create-cluster --cluster-name photo-gallery
```

2. **Build and push images to ECR:**

```bash
# Create ECR repositories
aws ecr create-repository --repository-name photo-gallery-backend
aws ecr create-repository --repository-name photo-gallery-frontend

# Get login token
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build and push
docker build -t photo-gallery-backend -f backend/Dockerfile.prod backend/
docker tag photo-gallery-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/photo-gallery-backend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/photo-gallery-backend:latest

docker build -t photo-gallery-frontend -f frontend/Dockerfile.prod frontend/
docker tag photo-gallery-frontend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/photo-gallery-frontend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/photo-gallery-frontend:latest
```

3. **Create ECS task definition and service** (use AWS Console or CLI)

#### Using AWS App Runner

Create `apprunner.yaml`:

```yaml
version: 1.0
runtime: docker
build:
  commands:
    build:
      - echo "Building application..."
run:
  runtime-version: latest
  command: gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
  network:
    port: 8000
    env:
      - DATABASE_URL
      - REDIS_URL
      - SECRET_KEY
      - AWS_ACCESS_KEY_ID
      - AWS_SECRET_ACCESS_KEY
      - S3_BUCKET_NAME
```

### Google Cloud Platform

#### Using Cloud Run

1. **Build and push to Container Registry:**

```bash
# Configure Docker for GCP
gcloud auth configure-docker

# Build and push backend
docker build -t gcr.io/your-project/photo-gallery-backend -f backend/Dockerfile.prod backend/
docker push gcr.io/your-project/photo-gallery-backend

# Build and push frontend
docker build -t gcr.io/your-project/photo-gallery-frontend -f frontend/Dockerfile.prod frontend/
docker push gcr.io/your-project/photo-gallery-frontend
```

2. **Deploy to Cloud Run:**

```bash
# Deploy backend
gcloud run deploy photo-gallery-backend \
  --image gcr.io/your-project/photo-gallery-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated

# Deploy frontend
gcloud run deploy photo-gallery-frontend \
  --image gcr.io/your-project/photo-gallery-frontend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### DigitalOcean App Platform

Create `.do/app.yaml`:

```yaml
name: photo-gallery
services:
- name: backend
  source_dir: backend
  dockerfile_path: Dockerfile.prod
  http_port: 8000
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: DATABASE_URL
    value: ${db.DATABASE_URL}
  - key: REDIS_URL
    value: ${redis.REDIS_URL}
  - key: SECRET_KEY
    value: ${SECRET_KEY}

- name: frontend
  source_dir: frontend
  dockerfile_path: Dockerfile.prod
  http_port: 80
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: REACT_APP_API_URL
    value: ${backend.PUBLIC_URL}

databases:
- name: db
  engine: PG
  version: "13"
  size: basic-xs

- name: redis
  engine: REDIS
  version: "6"
  size: basic-xs
```

Deploy:

```bash
doctl apps create --spec .do/app.yaml
```

## Post-Deployment

### 1. Process Initial Photos

After deployment, process your event photos:

```bash
# Copy photos to server
scp -r /path/to/photos user@server:/app/uploads/

# SSH to server and run processing
ssh user@server
cd /app
python processing/process_photos.py uploads/ --storage s3 --s3-bucket your-bucket
```

### 2. Set Up Monitoring

#### Health Checks

The application provides health check endpoints:

- Backend: `http://your-domain.com/health`
- Frontend: `http://your-domain.com/health`

#### Logging

Logs are available via Docker:

```bash
# View all logs
docker-compose -f docker-compose.prod.yml logs

# View specific service logs
docker-compose -f docker-compose.prod.yml logs backend
docker-compose -f docker-compose.prod.yml logs frontend
```

#### Metrics

Consider setting up monitoring with:

- **Prometheus + Grafana** for metrics
- **ELK Stack** for log aggregation
- **Sentry** for error tracking

### 3. Backup Strategy

#### Database Backups

Automated backup script is included:

```bash
# Manual backup
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U gallery_user photo_gallery > backup.sql

# Restore from backup
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U gallery_user photo_gallery < backup.sql
```

#### File Backups

If using local storage, backup the static files:

```bash
# Backup static files
tar -czf static-backup-$(date +%Y%m%d).tar.gz static/
```

### 4. SSL Certificate Renewal

For Let's Encrypt certificates, set up auto-renewal:

```bash
# Add to crontab
0 12 * * * /usr/bin/certbot renew --quiet && docker-compose -f /path/to/docker-compose.prod.yml restart nginx
```

## Scaling

### Horizontal Scaling

Scale individual services:

```bash
# Scale backend
docker-compose -f docker-compose.prod.yml up -d --scale backend=3

# Scale with load balancer
# Update nginx upstream configuration
```

### Vertical Scaling

Update resource limits in `docker-compose.prod.yml`:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

## Troubleshooting

### Common Issues

1. **Database connection errors:**
   - Check PostgreSQL is running and accessible
   - Verify connection string and credentials

2. **Redis connection errors:**
   - Ensure Redis is running
   - Check Redis password configuration

3. **Image processing failures:**
   - Verify face_recognition dependencies are installed
   - Check available memory for processing

4. **Storage upload failures:**
   - Verify cloud storage credentials
   - Check bucket permissions and CORS settings

### Debug Commands

```bash
# Check service status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs --tail=100 backend

# Execute commands in containers
docker-compose -f docker-compose.prod.yml exec backend bash
docker-compose -f docker-compose.prod.yml exec postgres psql -U gallery_user photo_gallery

# Check resource usage
docker stats
```

## Security Considerations

1. **Use strong passwords** for database and Redis
2. **Enable HTTPS** with valid SSL certificates
3. **Configure firewall** to only allow necessary ports
4. **Regular security updates** for base images
5. **Secure cloud storage** with proper IAM policies
6. **Monitor access logs** for suspicious activity
7. **Use secrets management** for sensitive configuration

## Maintenance

### Regular Tasks

1. **Update dependencies** regularly
2. **Monitor disk space** for logs and uploads
3. **Review and rotate logs**
4. **Update SSL certificates**
5. **Backup database** regularly
6. **Monitor application performance**

### Updates

To update the application:

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
./scripts/deploy.sh production
```