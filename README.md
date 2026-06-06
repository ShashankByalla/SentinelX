# 🛡️ SentinelX — Automated Monitoring & Incident Response Platform

![Python](https://img.shields.io/badge/Language-Python-3776AB)
![Docker](https://img.shields.io/badge/Container-Docker-2496ED)
![AWS](https://img.shields.io/badge/Cloud-AWS%20EC2-FF9900)
![Nginx](https://img.shields.io/badge/Proxy-Nginx-009639)

SentinelX is a self-hosted automated monitoring and incident response platform.
It executes playbooks automatically based on metrics, exposes REST APIs for
observability, and runs behind a secured Nginx reverse proxy with HTTPS on AWS EC2.

---

## 🏗️ Architecture

```
Internet (HTTPS)
      │
      ▼
Nginx Reverse Proxy (SSL Termination)
      │
      ▼
SentinelX Agent (Python)
      ├── /health       → System health check
      ├── /metrics/json → Real-time metrics
      ├── /playbooks    → Playbook management
      └── /docs         → Swagger UI
      │
      ▼
Persistent Storage (Logs + Playbook Data)
```

---

## ✨ Features

- 🤖 **Automated Playbook Execution** — trigger runbooks on metric thresholds
- 📊 **Real-time Metrics API** — expose system metrics as JSON
- 🔍 **Health Monitoring** — continuous health check endpoints
- 📋 **Swagger UI** — interactive API documentation
- 🔒 **HTTPS/SSL** — Nginx reverse proxy with SSL termination
- 🐳 **Fully Containerized** — Docker + Docker Compose deployment
- ☁️ **AWS EC2 Deployed** — production cloud deployment
- 💾 **Persistent Storage** — logs and data survive container restarts

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python |
| Reverse Proxy | Nginx |
| Containerization | Docker, Docker Compose |
| Cloud | AWS EC2 |
| SSL/TLS | Self-signed certificates |
| API Docs | Swagger UI |
| Storage | Persistent Docker volumes |

---

## 🚀 Deployment

### Prerequisites
- Docker & Docker Compose
- AWS EC2 instance (or any Linux VM)

### 1. Clone the Repository

```bash
git clone https://github.com/ShashankByalla/SentinelX.git
cd SentinelX
```

### 2. Generate SSL Certificates

```bash
mkdir certs
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout certs/sentinelx.key \
  -out certs/sentinelx.crt \
  -subj "/CN=sentinelx"
```

### 3. Start SentinelX

```bash
docker compose up -d
```

### 4. Verify Containers

```bash
docker ps
docker compose logs -f
```

### 5. Access SentinelX

| Endpoint | URL |
|----------|-----|
| Swagger UI | `https://<EC2-IP>/docs` |
| Health Check | `https://<EC2-IP>/health` |
| Metrics | `https://<EC2-IP>/metrics/json` |
| Playbooks | `https://<EC2-IP>/playbooks` |

> **Note:** Self-signed certificate browser warning is expected. Proceed safely.

---

## 📁 Project Structure

```
SentinelX/
├── agent/                  # Core app code, playbooks, connectors
├── demo/                   # Demo apps for testing
├── sentinelx_logs/         # Persistent log storage
├── Dockerfile              # Container build
├── docker-compose.yml      # Multi-container orchestration
└── nginx.conf              # Reverse proxy + HTTPS config
```

> **Note:** `certs/` folder is not committed to git.
> Generate SSL certificates locally using the command above.

---

## 🔄 How Playbooks Work

1. Metrics endpoint collects system data continuously
2. SentinelX agent evaluates metrics against defined thresholds
3. When threshold is breached → playbook triggered automatically
4. Execution results logged to persistent storage
5. Full history accessible via `/playbooks` API

---

## 🌐 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | System health status |
| GET | `/metrics/json` | Real-time system metrics |
| GET | `/playbooks` | List all playbooks |
| POST | `/playbooks/{id}/execute` | Trigger a playbook |
| GET | `/docs` | Swagger UI |

---

## 📝 Notes

- Nginx automatically redirects HTTP → HTTPS
- Playbook data and logs are persisted across container restarts
- Trigger playbooks via Swagger UI to generate logs and test the system

---

## 👤 Author

**Shashank Byalla**
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue)](https://www.linkedin.com/in/shashankbyalla/)
```

---

## After Pasting:

1. Replace `your-linkedin` with your actual LinkedIn URL
2. Add topics on repo page: `python` `devops` `monitoring` `docker` `nginx` `aws` `sre` `playbook` `observability` `incident-response`
3. Make sure `certs/` is deleted and in `.gitignore` before making repo public again

This is your **#1 pinned repo** — it deserves this README! 🚀
