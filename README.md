# Document Archiving System

## Overview
A secure, containerized, multi-tier document archiving system built with Docker Compose. Implements private networking, HashiCorp Vault secrets management, MinIO S3-compatible object storage, PostgreSQL metadata database, and NGINX load balancing.

## Architecture
The system uses a two-network architecture:
- public-net: Only NGINX is exposed (port 80)
- private-net: All services communicate internally
- Vault manages all sensitive credentials
- NGINX load balances across 2 API replicas

```
User --> NGINX (public-net + private-net)
              |-> API Instance 1 (private-net) --> PostgreSQL (private-net)
              |-> API Instance 2 (private-net) --> MinIO (private-net)
                                              --> Vault (private-net)
```

## Prerequisites
- Docker Engine 24+
- Docker Compose v2+
- At least 4GB available RAM
- curl (for testing)

## Quick Start

```bash
# Clone the repository
git clone <repo-url>
cd document-archiving-system

# Copy environment file
cp .env.example .env

# Start the entire stack
docker compose up -d

# Wait for all services to become healthy (may take 1-2 minutes)
docker compose ps

# The system is ready when all services show 'healthy'
```

## API Usage

Upload a document:
```bash
curl -X POST -F "file=@README.md" http://localhost/documents
```

List all documents:
```bash
curl http://localhost/documents
```

Retrieve a document by ID:
```bash
curl http://localhost/documents/1
```

Verify load balancing:
```bash
for i in $(seq 1 10); do
  curl -s -o /dev/null -w "Request $i: X-Served-By=%{header:X-Served-By}\n" http://localhost/documents
done
```

## Vault Setup
Vault is initialized automatically by the vault-init container on first startup. The setup script:
1. Initializes Vault with a single unseal key
2. Unseals Vault
3. Enables the KV v2 secrets engine
4. Stores application secrets (database and MinIO credentials)

The vault keys are saved to a Docker volume and shared read-only with services that need them.

To manually run the vault setup script:
```bash
docker compose run --rm vault-init
```

## Security Architecture
- Network isolation: Backend services are not directly accessible from outside
- Secrets management: No credentials in docker-compose.yml; all fetched from Vault at runtime
- Private bucket policy: MinIO documents bucket denies anonymous access
- Container scanning: API image scanned for vulnerabilities (see scan-report.txt)

## Project Structure
```
document-archiving-system/
├── api/                          # FastAPI application
│   ├── Dockerfile                # Container image definition
│   ├── requirements.txt          # Python dependencies
│   └── app/
│       ├── __init__.py
│       ├── main.py               # Application entry point, middleware, lifespan
│       ├── config.py             # Settings loaded from Vault
│       ├── vault_client.py       # Vault integration (hvac client)
│       ├── database.py           # PostgreSQL connection pool and queries
│       ├── storage.py            # MinIO object storage operations
│       └── routes.py             # API endpoint definitions
├── db-init/
│   └── init.sql                  # Creates the documents table on first boot
├── nginx/
│   └── nginx.conf                # Reverse proxy and load balancer config
├── scripts/
│   ├── setup_vault.sh            # Vault init, unseal, and secret population
│   ├── db-entrypoint.sh          # Fetches DB credentials from Vault
│   ├── minio-entrypoint.sh       # Fetches MinIO credentials from Vault
│   └── minio-init.sh             # Creates bucket and sets private policy
├── vault-config/
│   └── vault.hcl                 # Vault server configuration
├── docker-compose.yml            # Full stack orchestration
├── .env.example                  # Environment variable documentation
├── .gitignore                    # Excluded files
├── README.md                     # This file
└── scan-report.txt               # Container vulnerability scan results
```

## Troubleshooting
- If services fail to start, check logs: `docker compose logs <service>`
- If Vault is sealed, the vault-init container will handle unsealing on startup
- If the API can't connect, verify all services are healthy: `docker compose ps`
- To reset everything: `docker compose down -v` (removes all volumes)

## Stopping the System
```bash
# Stop all services
docker compose down

# Stop and remove all data
docker compose down -v
```
