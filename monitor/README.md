# Monitor Lab (Prometheus + Alertmanager)

Extends the load balancer with health monitoring and alerts when a server goes down.

## How It Works

```
┌────────┐     ┌─────────┐     ┌───────────────────────┐
│ Client │────▶│  Nginx  │────▶│  Backend1/2/3        │
└────────┘     │  (LB)   │     │  (Flask + /metrics)   │
               └─────────┘     └───────────▲───────────┘
                                           │ scrape every 5s
                               ┌───────────┴───────────┐
                               │     Prometheus        │
                               │  (Metrics + Rules)    │
                               └───────────┬───────────┘
                                           │ alert if down
                               ┌───────────▼───────────┐
                               │    Alertmanager       │
                               │  (View alerts here)   │
                               └───────────────────────┘
```

```yaml
# prometheus.yml - Scrape backend servers every 5s
scrape_configs:
  - job_name: 'backends'
    static_configs:
      - targets: [backend1:5000, backend2:5000, backend3:5000]

# alert_rules.yml - Fire alert when server is down
- alert: BackendDown
  expr: up{job="backends"} == 0    # up=0 means server not responding
  for: 10s
  annotations:
    summary: "Backend server is DOWN!"
```

## Run the Lab

```bash
cd monitor
docker compose up --build
```

Wait for all services to start, then in another terminal:

```bash
chmod +x test.sh && ./test.sh
```

## Dashboards

| Service | URL | Description |
|---------|-----|-------------|
| Nginx (LB) | http://localhost:80 | Load balancer |
| Prometheus | http://localhost:9090 | Metrics & alert rules |
| Alertmanager | http://localhost:9093 | Active alerts |

## Test Manually

```bash
# 1. Check all backends are healthy
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {instance: .labels.instance, health: .health}'

# 2. Load balancer works
for i in {1..6}; do curl -s http://localhost:80/ | jq -r '.server'; done

# 3. Kill a backend - THIS TRIGGERS THE ALERT!
docker compose stop backend1

# 4. Check Prometheus alerts page (wait ~15 seconds)
# Open: http://localhost:9090/alerts
# Or via API:
curl -s http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | {alertname: .labels.alertname, state: .state}'

# 5. Check Alertmanager dashboard
# Open: http://localhost:9093
# Shows: BackendDown alert is FIRING

# 6. Load balancer continues with remaining backends
for i in {1..6}; do curl -s http://localhost:80/ | jq -r '.server'; done
# → Only backend2 and backend3 respond

# 7. Bring backend1 back
docker compose start backend1

# 8. Alert resolves automatically
```

## Alert Flow

```
Backend1 stops responding
        ↓
Prometheus detects up{backend1}=0 (scrapes every 5s)
        ↓
Wait 10 seconds (for: 10s in rule)
        ↓
Alert fires: BackendDown
        ↓
View in Prometheus: http://localhost:9090/alerts
View in Alertmanager: http://localhost:9093
```

## Prometheus Queries

Try these in Prometheus (http://localhost:9090):

```promql
# Check which backends are up (1) or down (0)
up{job="backends"}

# Total requests per server
app_requests_total

# Server uptime
app_uptime_seconds
```

## Key Takeaway

```
Without monitoring: Server dies → Nobody knows → Users complain
With monitoring:    Server dies → Prometheus detects → Alert fires → Fix immediately
```
