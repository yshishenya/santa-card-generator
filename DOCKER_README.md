# Docker Setup for Santa Project

This document describes the Docker configuration for the Santa AI Card Generator project.

## Overview

The Santa project consists of two main services:
- **Backend**: FastAPI application (Python 3.11+)
- **Frontend**: Vue.js 3 application with Vite

Both services are containerized and orchestrated using Docker Compose.

## Files Structure

```
santa/
├── docker-compose.yml          # Production configuration
├── docker-compose.dev.yml      # Development override
├── .env.example                # Environment variables template
├── .dockerignore               # Root-level Docker ignore
├── backend/
│   ├── Dockerfile              # Backend production image
│   ├── Dockerfile.dev          # Backend development image
│   ├── .dockerignore           # Backend-specific ignores
│   └── ...
└── frontend/
    ├── Dockerfile              # Frontend production image
    ├── Dockerfile.dev          # Frontend development image
    ├── .dockerignore           # Frontend-specific ignores
    └── ...
```

## Quick Start

### 1. Initial Setup

```bash
# Clone the repository
cd /home/yan/santa

# Copy environment template
cp .env.example .env

# Edit .env with your actual values
nano .env
```

Required environment variables:
- `GEMINI_API_KEY` - Your Google Gemini API key
- `TELEGRAM_BOT_TOKEN` - Your Telegram bot token
- `TELEGRAM_CHAT_ID` - Target chat ID
- `TELEGRAM_TOPIC_ID` - Target topic/thread ID

### 2. Production Mode

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Access:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

### 3. Development Mode

```bash
# Start with development configuration
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Or rebuild and start
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

Development mode features:
- Hot reload for both frontend and backend
- Source code mounted as volumes
- Debug mode enabled
- Vite dev server on port 5173

Access:
- Frontend (Vite HMR): http://localhost:5173
- Backend (with reload): http://localhost:8000

## Docker Compose Configuration

### docker-compose.yml (Production)

Main configuration file with:
- **Backend service**:
  - Builds from `./backend/Dockerfile`
  - Exposes port 8000
  - Health checks enabled
  - Data volume mounted for employee list

- **Frontend service**:
  - Builds from `./frontend/Dockerfile`
  - Exposes port 3000 (nginx)
  - Depends on backend health check

- **Networking**: Isolated bridge network

### docker-compose.dev.yml (Development Override)

Overrides production config with:
- Source code mounted as read-only volumes
- Hot reload enabled
- Debug logging
- Development commands
- Vite dev server for frontend

## Environment Variables

### Backend Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GEMINI_API_KEY` | Google Gemini API key | - | Yes |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | - | Yes |
| `TELEGRAM_CHAT_ID` | Target chat ID | - | Yes |
| `TELEGRAM_TOPIC_ID` | Thread/topic ID | 0 | No |
| `DEBUG` | Debug mode | false | No |
| `LOG_LEVEL` | Logging level | INFO | No |
| `MAX_REGENERATIONS` | Max card regenerations | 3 | No |
| `EMPLOYEES_FILE_PATH` | Employee list path | /app/data/employees.json | No |
| `CORS_ORIGINS` | Allowed CORS origins | localhost:3000 | No |

### Frontend Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `VITE_API_URL` | Backend API URL | http://localhost:8000 | Yes |
| `NODE_ENV` | Node environment | production | No |

## Common Commands

### Build and Run

```bash
# Build images
docker-compose build

# Build without cache
docker-compose build --no-cache

# Start in background
docker-compose up -d

# Start with logs
docker-compose up

# Restart services
docker-compose restart
```

### Logs and Debugging

```bash
# View all logs
docker-compose logs

# Follow logs
docker-compose logs -f

# Service-specific logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Last 100 lines
docker-compose logs --tail=100
```

### Maintenance

```bash
# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Execute command in running container
docker-compose exec backend bash
docker-compose exec frontend sh

# View running containers
docker-compose ps

# View resource usage
docker stats
```

## Health Checks

### Backend Health Check

Endpoint: `GET /health`

Docker health check:
- Interval: 30 seconds
- Timeout: 10 seconds
- Retries: 3
- Start period: 40 seconds

Test manually:
```bash
curl http://localhost:8000/health
```

### Frontend Dependency

Frontend waits for backend to be healthy before starting:
```yaml
depends_on:
  backend:
    condition: service_healthy
```

## Volumes

### Backend Data Volume

```yaml
volumes:
  - ./backend/data:/app/data
```

Stores:
- `employees.json` - Employee list
- Generated images (temporary)
- Application logs (if configured)

### Development Volumes

In dev mode, source code is mounted:

**Backend**:
```yaml
- ./backend/src:/app/src:ro
- ./backend/tests:/app/tests:ro
```

**Frontend**:
```yaml
- ./frontend/src:/app/src:ro
- ./frontend/public:/app/public:ro
```

## Networking

Custom bridge network `santa-network` isolates services:
- Services can communicate by name (e.g., `http://backend:8000`)
- External access only through exposed ports
- Secure inter-service communication

## Troubleshooting

### Backend won't start

```bash
# Check logs
docker-compose logs backend

# Common issues:
# 1. Missing .env file
cp .env.example .env

# 2. Port 8000 already in use
lsof -i :8000
# Kill the process or change port in docker-compose.yml

# 3. Rebuild image
docker-compose build --no-cache backend
```

### Frontend build fails

```bash
# Check logs
docker-compose logs frontend

# Common issues:
# 1. Node modules cache issue
docker-compose down
docker-compose build --no-cache frontend

# 2. Backend not accessible
# Ensure backend is running and healthy
docker-compose ps
```

### Hot reload not working in dev mode

```bash
# Ensure using dev compose file
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Check volume mounts
docker-compose -f docker-compose.yml -f docker-compose.dev.yml config

# Restart services
docker-compose restart
```

### Permission issues with volumes

```bash
# Fix ownership (Linux)
sudo chown -R $USER:$USER ./backend/data

# Or run with proper user in Dockerfile
```

## Production Deployment

### Prerequisites

1. Server with Docker and Docker Compose installed
2. Domain name configured (optional)
3. SSL certificates (for HTTPS)
4. Environment variables configured

### Steps

1. **Clone repository**:
   ```bash
   git clone <repo-url>
   cd santa
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   nano .env
   # Set production values
   ```

3. **Build images**:
   ```bash
   docker-compose build
   ```

4. **Start services**:
   ```bash
   docker-compose up -d
   ```

5. **Verify**:
   ```bash
   docker-compose ps
   docker-compose logs
   curl http://localhost:8000/health
   ```

### Optional: Nginx Reverse Proxy

For HTTPS and custom domain, add nginx service:

```yaml
nginx:
  image: nginx:alpine
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf
    - ./ssl:/etc/nginx/ssl
  depends_on:
    - backend
    - frontend
```

## Best Practices

1. **Never commit `.env` file** - Contains secrets
2. **Use `.dockerignore`** - Reduces build context size
3. **Multi-stage builds** - Smaller production images
4. **Health checks** - Ensure service reliability
5. **Resource limits** - Prevent container resource exhaustion
6. **Logging** - Centralized logging for debugging
7. **Secrets management** - Use Docker secrets in production

## Next Steps

- [ ] Create `backend/Dockerfile` for production build
- [ ] Create `backend/Dockerfile.dev` for development
- [ ] Create `frontend/Dockerfile` for production build
- [ ] Create `frontend/Dockerfile.dev` for development
- [ ] Configure nginx for frontend static files
- [ ] Set up CI/CD pipeline for automated builds
- [ ] Implement Docker secrets for sensitive data
- [ ] Add monitoring and logging solutions

## References

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Docker Deployment](https://fastapi.tiangolo.com/deployment/docker/)
- [Vite Docker Guide](https://vitejs.dev/guide/static-deploy.html)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
