# Photo Gallery Deployment Guide

## Pre-Deployment Checklist

1. **Environment Variables** - Update these for production:
   ```env
   DATABASE_URL=postgresql://user:password@your-db-host:5432/gallery
   REDIS_URL=redis://your-redis-host:6379
   API_HOST=0.0.0.0
   API_PORT=8000
   CORS_ORIGINS=https://your-domain.com
   ```

2. **Domain Setup**:
   - Buy a domain (e.g., photos.yourname.com)
   - Point DNS to your server IP

3. **Security**:
   - Change default database passwords
   - Set up SSL/HTTPS certificates
   - Add authentication (optional)

## Option 1: DigitalOcean App Platform (Recommended)

### Step 1: Prepare Repository
```bash
# Push your code to GitHub
git add .
git commit -m "Ready for deployment"
git push origin main
```

### Step 2: Create DigitalOcean App
1. Go to [DigitalOcean Apps](https://cloud.digitalocean.com/apps)
2. Click "Create App"
3. Connect your GitHub repository
4. Configure services:
   - **Backend**: `backend/` folder, port 8000
   - **Frontend**: `frontend/` folder, build command `npm run build`
   - **Database**: Add PostgreSQL database
   - **Redis**: Add Redis database

### Step 3: Environment Variables
Add these in the DigitalOcean dashboard:
```
DATABASE_URL=${db.DATABASE_URL}
REDIS_URL=${redis.DATABASE_URL}
CORS_ORIGINS=https://your-app-name.ondigitalocean.app
```

### Step 4: Deploy
- Click "Create Resources"
- Wait 5-10 minutes for build
- Your app will be live at `https://your-app-name.ondigitalocean.app`

## Option 2: VPS Deployment (More Control)

### Step 1: Get VPS
1. Create DigitalOcean Droplet (Ubuntu 22.04, $10/month)
2. SSH into server: `ssh root@your-server-ip`

### Step 2: Install Dependencies
```bash
# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose-plugin -y

# Install Nginx (for reverse proxy)
apt install nginx -y

# Install Certbot (for SSL)
apt install certbot python3-certbot-nginx -y
```

### Step 3: Upload Your Code
```bash
# On your local machine
scp -r /path/to/photos root@your-server-ip:/app

# Or use git
cd /app
git clone https://github.com/yourusername/photo-gallery.git
cd photo-gallery
```

### Step 4: Configure Production
```bash
# Create production docker-compose
cp docker-compose.yml docker-compose.prod.yml

# Edit for production
nano docker-compose.prod.yml
```

Update ports and add restart policies:
```yaml
version: '3.8'
services:
  frontend:
    restart: unless-stopped
    ports:
      - "3000:3000"

  backend:
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - CORS_ORIGINS=https://your-domain.com

  postgres:
    restart: unless-stopped
    # Remove port exposure for security

  redis:
    restart: unless-stopped
    # Remove port exposure for security
```

### Step 5: Set Up Nginx Reverse Proxy
```bash
# Create Nginx config
nano /etc/nginx/sites-available/photo-gallery
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Static files
    location /static/ {
        proxy_pass http://localhost:8000/static/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # File uploads (large files)
    client_max_body_size 100M;
}
```

```bash
# Enable site
ln -s /etc/nginx/sites-available/photo-gallery /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

### Step 6: Deploy Application
```bash
# Start all services
docker compose -f docker-compose.prod.yml up -d

# Check status
docker ps
```

### Step 7: Set Up SSL
```bash
# Get SSL certificate
certbot --nginx -d your-domain.com

# Test auto-renewal
certbot renew --dry-run
```

## Post-Deployment Steps

### 1. Upload Photos
```bash
# Copy your photos to the server
scp -r /path/to/your/photos/* root@your-server-ip:/app/uploads/
```

### 2. Process Photos
```bash
# SSH into server and run processing
docker exec photos-backend-1 python complete_fresh_process_fixed.py
```

### 3. Set Up Download Feature

Add download endpoints to your backend API:

```python
# In backend/app/routers/photos.py
@router.get("/download/{photo_id}")
async def download_photo(photo_id: str, db: Session = Depends(get_db)):
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    file_path = f"/app/static/original/{photo.filename}"
    return FileResponse(
        file_path,
        media_type='image/jpeg',
        filename=photo.filename
    )

@router.get("/download/person/{person_id}")
async def download_person_photos(person_id: str, db: Session = Depends(get_db)):
    # Create ZIP file with all photos for a person
    photos = db.query(Photo).join(FaceDetection).filter(
        FaceDetection.person_id == person_id
    ).all()

    # Create temporary ZIP file
    import zipfile
    import tempfile

    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
        with zipfile.ZipFile(tmp_file, 'w') as zip_file:
            for photo in photos:
                file_path = f"/app/static/original/{photo.filename}"
                zip_file.write(file_path, photo.filename)

        return FileResponse(
            tmp_file.name,
            media_type='application/zip',
            filename=f"person_{person_id}_photos.zip"
        )
```

### 4. Share with Everyone

**Send this to your friends:**
```
Hi! Check out our event photos at: https://your-domain.com

Instructions:
1. Click on your face to see all your photos
2. Click the download button to get your photos
3. You can also browse all photos in the gallery

Enjoy! 📸
```

## Monitoring & Maintenance

### Check Application Status
```bash
# View logs
docker logs photos-backend-1
docker logs photos-frontend-1

# Monitor resources
docker stats

# Backup database
docker exec photos-postgres-1 pg_dump -U gallery_user photo_gallery > backup.sql
```

### Update Application
```bash
# Pull latest code
git pull

# Rebuild and restart
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d --build
```

## Cost Estimation

### DigitalOcean App Platform
- **Small**: $25/month (good for 500+ photos)
- **Medium**: $50/month (good for 2000+ photos)

### VPS Option
- **Droplet**: $10/month
- **Domain**: $10-15/year
- **Total**: ~$12/month

## Security Notes

1. **Change default passwords** in production
2. **Set up firewall** to only allow HTTP/HTTPS
3. **Regular backups** of database and photos
4. **Monitor disk space** (photos take up space!)

Choose DigitalOcean App Platform if you want simplicity, or VPS if you want control and lower costs.