# Production Deployment Guide

## Quick Start

```bash
# 1. Copy environment template
cp .env.production.example .env

# 2. Edit .env with production values (must set all required variables)

# 3. Build and start services
docker compose -f docker-compose.prod.yml up -d --build

# 4. Check status
docker compose -f docker-compose.prod.yml ps

# 5. View logs
docker compose -f docker-compose.prod.yml logs -f
```

## Required Environment Variables

| Variable | Description |
|----------|-------------|
| `POSTGRES_PASSWORD` | PostgreSQL password |
| `ADMIN_API_KEY` | Admin API key |
| `JWT_SECRET_KEY` | JWT signing key |

## Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DOCKER_REGISTRY` | `mbabic84` | Docker registry for images |
| `IMAGE_TAG` | `latest` | Image tag |
| `MCP_SERVER_PORT` | `8000` | MCP server port |
| `REST_API_PORT` | `8001` | REST API port |
| `LOG_LEVEL` | `info` | Logging level |

## Health Checks

All services include health checks. Use `--wait` to wait for healthy:

```bash
docker compose -f docker-compose.prod.yml up -d --wait
```

## Scaling

Scale services horizontally:

```bash
docker compose -f docker-compose.prod.yml up -d --scale mcp_server=2
```

Note: Requires a load balancer in front for TCP routing.

## Updates

```bash
# Pull latest images and rebuild
docker compose -f docker-compose.prod.yml up -d --build

# Or pull only (if using pre-built images)
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

## Backup

```bash
# Backup PostgreSQL
docker compose -f docker-compose.prod.yml exec postgres pg_dump -U ainstruct ainstruct > backup.sql

# Backup Qdrant
docker compose -f docker-compose.prod.yml stop qdrant
docker cp $(docker compose -f docker-compose.prod.yml ps -q qdrant):/qdrant/storage ./qdrant_backup
docker compose -f docker-compose.prod.yml start qdrant
```

## Stopping

```bash
docker compose -f docker-compose.prod.yml down
```

For data persistence:

```bash
docker compose -f docker-compose.prod.yml down -v  # WARNING: deletes all data
```
