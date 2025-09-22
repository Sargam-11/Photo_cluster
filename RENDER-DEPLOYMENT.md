# 🆓 Deploy Photo Gallery on Render (FREE)

Deploy your photo gallery **completely FREE** using Render's free tier!

## 🎯 FREE Hosting with Render

### **Cost**: $0/month
- ✅ **750 hours/month FREE** (enough for small/medium usage)
- ✅ **PostgreSQL database included**
- ✅ **Automatic HTTPS**
- ✅ **Auto-deploy from Git**
- ✅ **Apps sleep after 15min inactivity** (wake up automatically)

## 🚀 Step-by-Step Deployment

### Part 1: Prepare Your Code

#### 1. Commit Your Changes
```bash
git init
git add .
git commit -m "Initial photo gallery setup"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

### Part 2: Deploy Backend on Render

#### 1. Sign Up for Render
- Go to [render.com](https://render.com)
- Sign up with GitHub (free account)

#### 2. Create PostgreSQL Database
1. Click **"New +"** → **"PostgreSQL"**
2. Configure:
   - **Name**: `photo-gallery-db`
   - **Database**: `photo_gallery`
   - **User**: `photo_gallery_user`
   - **Region**: Choose closest to you
   - **Plan**: **Free** ($0/month)
3. Click **"Create Database"**
4. **Save the connection details** (you'll need them)

#### 3. Deploy Backend Service
1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository
3. Configure:
   - **Name**: `photo-gallery-backend`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: **Free** ($0/month)

#### 4. Set Environment Variables
In your backend service dashboard, add these environment variables:

```env
DATABASE_URL=postgresql://photo_gallery_user:PASSWORD@HOST/photo_gallery
CORS_ORIGINS=https://YOUR-FRONTEND-APP.vercel.app
API_HOST=0.0.0.0
API_PORT=10000
FACE_DETECTION_MODEL=hog
CLUSTERING_EPS=0.4
CLUSTERING_MIN_SAMPLES=2
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE=50MB
ALLOWED_EXTENSIONS=jpg,jpeg,png,heic
```

**Note**: Replace `DATABASE_URL` with the connection string from your PostgreSQL database.

### Part 3: Deploy Frontend on Vercel

#### 1. Install Vercel CLI
```bash
npm install -g vercel
```

#### 2. Deploy Frontend
```bash
cd frontend

# Login to Vercel
vercel login

# Deploy
vercel

# Set environment variable
vercel env add REACT_APP_API_URL
# Enter: https://YOUR-BACKEND-APP.onrender.com
```

#### 3. Update Backend CORS
Go back to your Render backend and update the `CORS_ORIGINS` environment variable:
```env
CORS_ORIGINS=https://YOUR-FRONTEND-APP.vercel.app
```

### Part 4: Upload and Process Photos

#### Option 1: Manual Upload (Recommended for First Deployment)
1. **Prepare photos locally**:
   ```bash
   # Run processing locally first (much faster)
   docker-compose up -d
   docker exec photos-backend-1 python complete_fresh_process_fixed.py
   ```

2. **Export processed data**:
   ```bash
   # Export database
   docker exec photos-db-1 pg_dump -U postgres photo_gallery > gallery_data.sql

   # Create tar of processed images
   docker exec photos-backend-1 tar -czf /app/processed_images.tar.gz -C /app faces uploads
   docker cp photos-backend-1:/app/processed_images.tar.gz .
   ```

3. **Import to Render**:
   ```bash
   # Connect to Render database
   psql "YOUR_RENDER_DATABASE_URL"

   # Import data
   \i gallery_data.sql
   ```

#### Option 2: Upload Interface (Future Enhancement)
Add an upload page to your frontend for users to upload photos directly.

## 🎯 Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   PostgreSQL    │
│   (Vercel)      │────│   (Render)      │────│   (Render)      │
│   React App     │    │   FastAPI       │    │   Database      │
│   FREE          │    │   FREE          │    │   FREE          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 💰 Cost Breakdown

### Completely FREE Option:
- **Frontend (Vercel)**: $0/month
- **Backend (Render)**: $0/month (750 hours free)
- **Database (Render)**: $0/month
- **Custom Domain**: $0/month (render.com + vercel.app subdomains)
- **Total**: **$0/month**

### Notes:
- **Free tier limits**: 750 hours/month (≈25 hours/day)
- **Apps sleep after 15min** of inactivity
- **Wake-up time**: ~30 seconds when accessed
- **Database**: 1GB storage limit on free tier

## 🔧 Deployment Commands

### Deploy Backend:
1. Push code to GitHub
2. Render auto-deploys from main branch
3. Check logs in Render dashboard

### Deploy Frontend:
```bash
cd frontend
vercel --prod
```

### Update Deployment:
```bash
# Backend: Just push to GitHub
git push origin main

# Frontend: Redeploy
cd frontend
vercel --prod
```

## 🌟 What Users Can Do

Once deployed, users can:

1. **Browse all photos** in the gallery
2. **Find themselves** using face recognition
3. **View their photos** by clicking their face card
4. **Download individual photos** (right-click save)
5. **Download ALL their photos** as a ZIP file (web quality)
6. **Download original quality** ZIP files
7. **Share the link** with friends and family

## 📱 Share Your Gallery

Once deployed, share this with everyone:

```
🎉 Event Photos Are Ready!

View and download your photos at:
https://your-app-name.vercel.app

Instructions:
1. Click on your face to see all your photos
2. Click "Download Photos" to get a ZIP file
3. Click "Download Original" for full-quality photos

Enjoy! 📸
```

## 🚨 Important Notes

1. **Free tier limitations**:
   - Backend sleeps after 15min inactivity
   - 750 hours/month limit
   - 1GB database storage

2. **Performance**:
   - First load after sleep: ~30 seconds
   - Regular loads: Fast

3. **Scaling**:
   - Can upgrade to paid plans later
   - Render: $7/month for always-on
   - Vercel: Always free for personal projects

4. **Security**:
   - Photos are public (anyone with link can access)
   - No authentication (can be added later)

This setup gives you a **professional photo gallery** that costs $0 to run and can handle most events!