# learning-by-practice

Hands-on labs for backend infrastructure concepts.

## Labs

### 1. [Cache (Redis)](./cache/README.md)
- **DB Caching** - Reduce database load with Redis cache
- **Cache Invalidation** - TTL vs manual invalidation
- **Session Sharing** - Share sessions across multiple app instances

### 2. [Load Balancer (Nginx)](./loadbalancer/README.md)
- Round-robin distribution across multiple backends

### 3. [Monitor (Prometheus + Alertmanager)](./monitor/README.md)
- Health checks with Prometheus
- Alert rules when server goes down
- Metrics collection (`/metrics` endpoint)

### 4. [Reverse Proxy (Nginx + SSL)](./reverse-proxy/README.md)
- SSL termination at reverse proxy
- Self-signed certificate generation
- HTTP → HTTPS redirect
- Security headers

### 5. [Logging (ELK Stack)](./logging/README.md)
- Centralized logging with Elasticsearch, Kibana, Filebeat
- JSON structured logging for easy parsing
- Log aggregation from multiple app instances
- Search and visualize logs in Kibana

---

## Quick Start

Each lab runs with Docker Compose:

```bash
cd <lab-folder>
docker compose up --build
```