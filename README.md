# Sentinel

A real-time crisis intelligence platform that ingests, scores, and monitors disaster data from multiple sources with live alerting and visualization.

## Introduction

Sentinel is designed to help operations teams and emergency responders understand emerging natural risks (earthquakes, storms, floods) by combining:

- automatic data collection (USGS + OpenWeather)
- rule-based risk scoring and anomaly detection
- time-series prediction and statistical trend analysis
- real-time user interfaces via WebSocket and a modern dashboard
- production-ready infrastructure (Docker, Postgres, Redis, Celery, Nginx)

The system architecture is layered for maintainability: API, services, workers, and data store.

## Demo Video

Below is the project demo video from the repository `assets` folder.

> Note: GitHub markdown does not always allow inline playback of local video files (it may sanitize or drop the `<video>` tag in the rendered view). If playback is not available in the UI, use the direct link or download the file.

<video controls width="820" height="460">
  <source src="assets/video.mp4" type="video/mp4">
  Your browser does not support the video tag. You can also view it directly at [assets/video.mp4](assets/video.mp4).
</video>

- Direct download/view link: [assets/video.mp4](assets/video.mp4)
- Alternative (GitHub-friendly): convert to GIF or upload to YouTube/Vimeo and link/embed a thumbnail.

## Features

### Backend (Python/FastAPI)
- **API Integration**: USGS Earthquake API and OpenWeatherMap API with retry logic and rate limiting
- **Risk Engine**: Rule-based scoring with strategy pattern for earthquakes, storms, and floods
- **Anomaly Detection**: Moving average and deviation detection for spike identification
- **Prediction Module**: Time-series forecasting using exponential weighted moving average
- **Alert System**: Real-time alerts via WebSocket, Redis pub/sub, and simulated SMS/Email
- **Background Tasks**: Celery workers for polling APIs and processing events

### Frontend (React/TypeScript)
- **Live Dashboard**: Real-time alert feed with severity color coding
- **Interactive Map**: Leaflet-based map visualization with marker clustering
- **WebSocket Updates**: Auto-reconnecting WebSocket client for live updates
- **Responsive Design**: Mobile-first design with TailwindCSS
- **State Management**: Zustand for global state, React Query for data fetching

### Infrastructure
- **Docker Compose**: Complete containerization setup
- **PostgreSQL**: Primary database with Alembic migrations
- **Redis**: Cache, pub/sub, and Celery broker
- **Nginx**: Reverse proxy configuration
- **Capacitor**: Mobile app support for Android and iOS

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │  React Web  │  │   Mobile    │  │   Third-party Apps     │ │
│  │  Dashboard  │  │ (Capacitor) │  │                         │ │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘ │
│         │                │                      │               │
│         └────────────────┼──────────────────────┘               │
│                          │                                      │
│                     WebSocket                                   │
└──────────────────────────┼──────────────────────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────────────┐
│                     API Gateway (Nginx)                          │
└──────────────────────────┼──────────────────────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────────────┐
│                       Backend Layer                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    FastAPI Server                         │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │   │
│  │  │  Alerts  │  │ Metrics  │  │ Health   │  │   WS     │ │   │
│  │  │  Routes  │  │ Routes   │  │ Routes   │  │ Handler  │ │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                              │                                   │
│  ┌───────────────────────────┼───────────────────────────────┐   │
│  │              Services Layer                                │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │   │
│  │  │ Risk     │  │ Anomaly  │  │Prediction│  │ Alert    │ │   │
│  │  │ Engine   │  │Detection │  │ Engine   │  │ Service  │ │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                              │                                   │
│  ┌───────────────────────────┼───────────────────────────────┐   │
│  │             Celery Workers                                │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐               │   │
│  │  │  USGS    │  │ Weather  │  │ Process  │               │   │
│  │  │  Poller  │  │ Poller   │  │ Events   │               │   │
│  │  └──────────┘  └──────────┘  └──────────┘               │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                              │                                   │
└──────────────────────────────┼───────────────────────────────────┘
                               │
┌──────────────────────────────┼───────────────────────────────────┐
│                         Data Layer                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │ PostgreSQL  │  │    Redis    │  │   External APIs         │ │
│  │  (Primary)  │  │ (Cache/Pub) │  │ (USGS, OpenWeather)     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### Running with Docker (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/yourusername/disaster-detector.git
cd disaster-detector
```

2. Create environment files:
```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your configuration
```

3. Start all services:
```bash
npm start
# or
docker-compose -f infra/docker-compose.yml up -d
```

4. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Local Development

1. Start the backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

2. Start the frontend:
```bash
cd frontend
npm install
npm run dev
```

3. Start Celery worker (optional):
```bash
cd backend
celery -A app.workers.celery_app worker --loglevel=info
```

## API Endpoints

### Alerts
- `GET /api/v1/alerts` - List alerts with filtering and pagination
- `GET /api/v1/alerts/active` - Get active alerts
- `GET /api/v1/alerts/stats` - Get alert statistics
- `GET /api/v1/alerts/{id}` - Get specific alert
- `POST /api/v1/alerts` - Create new alert
- `PATCH /api/v1/alerts/{id}` - Update alert
- `POST /api/v1/alerts/{id}/acknowledge` - Acknowledge alert

### Metrics
- `GET /api/v1/metrics` - System metrics
- `GET /api/v1/metrics/hourly` - Hourly metrics
- `GET /api/v1/metrics/severity-trend` - Severity trend

### Health
- `GET /api/v1/health` - Health check
- `GET /api/v1/ready` - Readiness check

### WebSocket
- `WS /api/v1/ws` - Real-time alert stream

## Project Structure

```
disaster_detector/
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── main.py         # FastAPI application
│   │   ├── core/           # Configuration and utilities
│   │   ├── db/             # Database session and models
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic services
│   │   ├── api/            # API routes
│   │   └── workers/        # Celery tasks
│   ├── alembic/            # Database migrations
│   └── requirements.txt
├── frontend/               # React TypeScript frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── hooks/          # Custom React hooks
│   │   ├── store/          # Zustand store
│   │   └── services/       # API services
│   └── package.json
├── infra/                  # Infrastructure configuration
│   ├── docker-compose.yml
│   └── nginx.conf
└── package.json           # Root package.json
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection URL | - |
| `REDIS_URL` | Redis connection URL | - |
| `USGS_API_BASE_URL` | USGS Earthquake API URL | - |
| `OPENWEATHER_API_KEY` | OpenWeather API key | - |
| `CELERY_BROKER_URL` | Celery broker URL | - |

See `backend/.env.example` for all configuration options.

## Mobile Development

This application supports mobile deployment via Capacitor:

```bash
# Add Android platform
npm run mobile:android

# Add iOS platform
npm run mobile:ios

# Sync Capacitor
npm run mobile:sync

# Open in Android Studio
npm run mobile:open:android

# Open in Xcode
npm run mobile:open:ios
```

## Testing

```bash
# Run all tests
npm test

# Backend tests only
npm run test:backend

# Frontend tests only
npm run test:frontend
```

## Deployment

### Production Deployment

1. Set production environment variables in `backend/.env`
2. Build and start services:
```bash
docker-compose -f infra/docker-compose.yml up -d --build
```

3. Run database migrations:
```bash
docker-compose exec backend alembic upgrade head
```

### Scaling

The system supports horizontal scaling:
- Backend: Add more FastAPI containers behind Nginx
- Celery Workers: Add more worker containers
- Redis: Configure Redis Cluster for high availability

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -am 'Add my feature'`
4. Push to branch: `git push origin feature/my-feature`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [USGS Earthquake Hazards Program](https://earthquake.usgs.gov/) for earthquake data
- [OpenWeatherMap](https://openweathermap.org/) for weather data
- [Leaflet](https://leafletjs.com/) for map visualization
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework
- [React](https://reactjs.org/) for the frontend framework
