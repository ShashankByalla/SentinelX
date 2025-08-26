# SentinelX Deployment

## Project Overview
SentinelX is an automated monitoring and playbook execution platform. 
It provides APIs to execute playbooks, collect metrics, and manage logs.

## Directory Structure
- `Dockerfile` → builds the SentinelX container
- `docker-compose.yml` → runs SentinelX + Nginx reverse proxy
- `nginx.conf` → reverse proxy with HTTPS
- `certs/` → self-signed SSL certificate
- `agent/` → main app code, playbooks, connectors
- `demo/` → demo apps for testing
- `sentinelx_data/` → persistent storage for playbook data
- `sentinelx_logs/` → persistent storage for logs

## Deployment Instructions

1. Navigate to the project folder:
```bash
cd /root/sentinelx

2. Start SentinelX with Docker Compose:

docker-compose up -d

3. Verify containers are running:

docker ps
docker-compose logs -f

4.  Access SentinelX:

  • Swagger UI: https://<EC2-Public-IP>/docs
  • Health endpoint: https://<EC2-Public-IP>/health
  • Metrics endpoint: https://<EC2-Public-IP>/metrics/json
  • Playbooks endpoint: https://<EC2-Public-IP>/playbooks

5.  Trigger a playbook or action using Swagger UI to generate logs/data.

 Notes
    • Nginx redirects HTTP → HTTPS.
    • Data and logs are persisted in sentinelx_data/ and sentinelx_logs/.
    • Self-signed certificate warning is normal for HTTPS access.

---
