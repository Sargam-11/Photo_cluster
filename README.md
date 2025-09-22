# Personal Event Photo Gallery with Smart Face Recognition

Transform your event photo collection into an intelligent, personalized gallery where each attendee can instantly find all photos they appear in.

## Features

- **Smart Face Recognition**: Automatically detects and groups faces in event photos
- **Privacy-First**: Attendees only see photos they appear in
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Easy Setup**: One-time processing creates lasting value for everyone
- **Fast Performance**: Optimized image delivery with CDN support

## Architecture

- **Frontend**: React + TypeScript + Tailwind CSS
- **Backend**: FastAPI + Python
- **Database**: PostgreSQL + Redis caching
- **Processing**: face_recognition library + DBSCAN clustering
- **Storage**: AWS S3 or Cloudinary with CDN

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for local development)

### Development Setup

1. **Clone and setup environment**:
   ```bash
   git clone <repository-url>
   cd personal-event-photo-gallery
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Start services with Docker**:
   ```bash
   docker-compose up -d
   ```

3. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Local Development

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### Frontend Setup
```bash
cd frontend
npm install
npm start
```

#### Processing Pipeline Setup
```bash
cd processing
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

### Processing Event Photos

1. **Upload photos** to the `uploads/` directory
2. **Run the processing pipeline**:
   ```bash
   cd processing
   python process_photos.py --input ../uploads --batch-size 10
   ```
3. **Access the gallery** at http://localhost:3000

### Gallery Experience

1. **Homepage**: View face thumbnails labeled "Person 1", "Person 2", etc.
2. **Person Gallery**: Click on a face to see all photos containing that person
3. **Photo Viewer**: Full-screen viewing with download options

## Project Structure

```
personal-event-photo-gallery/
├── frontend/                 # React application
│   ├── src/
│   ├── public/
│   └── package.json
├── backend/                  # FastAPI application
│   ├── app/
│   ├── tests/
│   └── requirements.txt
├── processing/               # Photo processing pipeline
│   ├── services/
│   ├── tests/
│   └── requirements.txt
├── uploads/                  # Photo upload directory
├── docker-compose.yml        # Development environment
└── README.md
```

## Configuration

See `.env.example` for all available configuration options including:
- Database connections
- Storage providers (S3/Cloudinary)
- Face recognition parameters
- API settings

## Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# Processing tests
cd processing
pytest
```

## Deployment

See deployment documentation in `docs/deployment.md` for production setup instructions.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.