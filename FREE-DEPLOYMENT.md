# 🆓 FREE Photo Gallery Deployment Guide

Deploy your photo gallery **completely FREE** using modern hosting platforms!

## 🎯 FREE Hosting Strategy

### **Frontend**: Vercel (Free Tier)
- ✅ **$0/month** - 100GB bandwidth
- ✅ **Custom domain included**
- ✅ **Automatic HTTPS**
- ✅ **Global CDN**

### **Backend**: Railway (Free Tier)
- ✅ **$5 free credits monthly** (covers small apps)
- ✅ **PostgreSQL database included**
- ✅ **Redis included**
- ✅ **Easy deployment**

### **Alternative Backend**: Render (Free Tier)
- ✅ **750 hours/month FREE**
- ✅ **PostgreSQL database included**
- ✅ **Automatic sleep after 15min inactivity**

## 🚀 Step-by-Step Deployment

### Part 1: Prepare for Deployment

#### 1. Create Production Environment Files

Create `frontend/.env.production`:
```env
REACT_APP_API_URL=https://your-backend-app.railway.app/api
```

Create `backend/.env.production`:
```env
DATABASE_URL=${DATABASE_URL}
REDIS_URL=${REDIS_URL}
CORS_ORIGINS=https://your-frontend-app.vercel.app
API_HOST=0.0.0.0
API_PORT=8000
```

#### 2. Frontend Configuration (Create React App)

No additional configuration needed - the frontend is already configured with:
- Environment variable: `REACT_APP_API_URL`
- Tailwind CSS for styling
- TypeScript support
- Production build optimization

### Part 2: Deploy Backend to Railway (FREE)

#### 1. Sign up for Railway
- Go to [railway.app](https://railway.app)
- Sign up with GitHub (free)

#### 2. Deploy Backend
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Create new project
railway new

# Link to your backend
cd backend
railway link

# Add PostgreSQL database
railway add postgresql

# Add Redis
railway add redis

# Deploy backend
railway up
```

#### 3. Set Environment Variables in Railway Dashboard
```env
CORS_ORIGINS=https://your-app-name.vercel.app
DATABASE_URL=${DATABASE_URL}  # Auto-set by Railway
REDIS_URL=${REDIS_URL}        # Auto-set by Railway
```

#### 4. Upload Photos to Railway
```bash
# Create uploads folder and copy photos
railway run bash
mkdir -p /app/uploads
# Upload your photos here (you can use railway volumes)
```

### Part 3: Deploy Frontend to Vercel (FREE)

#### 1. Install Vercel CLI
```bash
npm install -g vercel
```

#### 2. Deploy Frontend
```bash
cd frontend

# Login to Vercel
vercel login

# Deploy (follow prompts)
vercel

# Set production environment variable
vercel env add REACT_APP_API_URL
# Enter: https://your-backend-app.railway.app/api
```

#### 3. Update Backend CORS
Update your Railway backend environment:
```env
CORS_ORIGINS=https://your-app-name.vercel.app
```

### Part 4: Alternative - Render (FREE)

If Railway doesn't work, use Render:

#### 1. Backend on Render
- Go to [render.com](https://render.com)
- Connect GitHub repository
- Create new **Web Service**
- Set build command: `pip install -r requirements.txt`
- Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Add **PostgreSQL database** (free tier)

#### 2. Environment Variables on Render
```env
DATABASE_URL=${DATABASE_URL}  # Auto-set by Render
CORS_ORIGINS=https://your-app-name.vercel.app
PORT=10000
```

## 🔧 Photo Upload & Processing

### Option 1: Upload via Web Interface (Add Later)
Add upload functionality to your frontend.

### Option 2: Manual Upload to Server
```bash
# Railway
railway run bash
# Copy photos to /app/uploads/

# Render
# Use Render's file upload or connect to external storage
```

### Option 3: Use Cloud Storage (Recommended)
Update your app to use **Cloudinary** (free tier):

Add to `backend/.env`:
```env
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

## 💡 Cost Breakdown

### Completely FREE Option:
- **Frontend (Vercel)**: $0/month
- **Backend (Railway)**: $0/month (with $5 monthly credits)
- **Database**: $0/month (included)
- **Domain**: $0/month (vercel.app subdomain)
- **Total**: **$0/month**

### Small Monthly Cost Option:
- **Frontend (Vercel)**: $0/month
- **Backend (Railway)**: ~$10/month (after free credits)
- **Custom Domain**: ~$12/year
- **Total**: ~$11/month

## 🎨 Frontend Updates for Production

Add download buttons to your frontend. Update `frontend/src/components/PersonCard.tsx`:

```typescript
import { useState } from 'react';

export default function PersonCard({ person }: { person: Person }) {
  const [downloading, setDownloading] = useState(false);

  const downloadPhotos = async (quality: 'original' | 'web' | 'thumbnail') => {
    setDownloading(true);
    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_URL}/persons/${person.id}/download?quality=${quality}`
      );

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `person_photos_${quality}.zip`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Download failed:', error);
    }
    setDownloading(false);
  };

  return (
    <div className="person-card">
      <img src={person.thumbnail_url} alt="Person" />
      <p>{person.photo_count} photos</p>

      {/* Download Buttons */}
      <div className="download-buttons">
        <button
          onClick={() => downloadPhotos('web')}
          disabled={downloading}
          className="bg-blue-500 text-white px-3 py-1 rounded"
        >
          {downloading ? 'Preparing...' : 'Download Photos'}
        </button>

        <button
          onClick={() => downloadPhotos('original')}
          disabled={downloading}
          className="bg-green-500 text-white px-3 py-1 rounded ml-2"
        >
          {downloading ? 'Preparing...' : 'Download Original'}
        </button>
      </div>
    </div>
  );
}
```

## 🔄 Deployment Commands Quick Reference

### Initial Deploy:
```bash
# Backend to Railway
cd backend
railway up

# Frontend to Vercel
cd frontend
vercel --prod
```

### Update Deployment:
```bash
# Update backend
cd backend
railway up

# Update frontend
cd frontend
vercel --prod
```

## 🎯 What Users Can Do:

1. **Browse all photos** in the gallery
2. **Find themselves** using face recognition
3. **View their photos** by clicking their face card
4. **Download individual photos** (right-click save)
5. **Download ALL their photos** as a ZIP file (web quality)
6. **Download original quality** ZIP file
7. **Share the link** with friends and family

## 📱 Sharing Your Gallery

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

1. **Free tiers have limits** - may need to upgrade for large events
2. **Processing must be done locally** first, then upload results
3. **Photos are public** - anyone with the link can access
4. **No authentication** in this version (can be added later)

This setup gives you a **professional photo gallery** that costs $0 to run!