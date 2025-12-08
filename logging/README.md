# Centralized Logging with ELK Stack

Learn how to deploy Elasticsearch, Kibana, and Filebeat for centralized log management.

## Architecture

```
┌─────────────┐     ┌─────────────┐
│    App 1    │     │    App 2    │
│  (Flask)    │     │  (Flask)    │
└──────┬──────┘     └──────┬──────┘
       │                   │
       │  JSON Logs        │
       ▼                   ▼
┌─────────────────────────────────┐
│         Shared Volume           │
│       /var/log/app/*.log        │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│           Filebeat              │
│    (Log Shipper / Agent)        │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│         Elasticsearch           │
│    (Storage & Search Engine)    │
│         Port: 9200              │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│            Kibana               │
│   (Visualization Dashboard)     │
│         Port: 5601              │
└─────────────────────────────────┘
```

## Components

| Component | Purpose | Port |
|-----------|---------|------|
| **Elasticsearch** | Stores and indexes logs | 9200 |
| **Kibana** | Web UI for searching and visualizing logs | 5601 |
| **Filebeat** | Agent that ships logs to Elasticsearch | - |
| **App 1 & 2** | Sample Flask apps generating logs | 5000 |

## Why Centralized Logging?

### Without Centralized Logging
```
Developer: "There's an error in production!"
Team: *SSH into server1* "Not here..."
Team: *SSH into server2* "Not here..."
Team: *SSH into server3* "Found it... but related errors are on server1"
```

### With Centralized Logging
```
Developer: "There's an error in production!"
Team: *Opens Kibana* → Search "level:error" → See all errors across all servers
```

## Quick Start

### 1. Start the Stack

```bash
docker-compose up -d
```

Wait for Elasticsearch to be healthy (about 30-60 seconds):
```bash
docker-compose logs -f elasticsearch
# Wait for "started" message
```

### 2. Access Services

- **Kibana**: http://localhost:5601
- **Elasticsearch**: http://localhost:9200

### 3. Generate Some Logs

```bash
# Basic requests
curl http://localhost:5000/
curl http://localhost:5000/user/123

# Generate warning logs (slow endpoint)
curl http://localhost:5000/slow

# Generate error logs
curl http://localhost:5000/error

# Generate multiple random logs
curl "http://localhost:5000/generate?count=50"
```

### 4. View Logs in Kibana

1. Open http://localhost:5601
2. Go to **Menu** → **Discover**
3. Create Data View:
   - Click "Create data view"
   - Name: `app-logs`
   - Index pattern: `app-logs-*`
   - Timestamp field: `@timestamp`
   - Click "Save"
4. Now you can search and filter logs!

## Log Format

The application uses JSON structured logging:

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "app": "app1",
  "message": "GET /user/123 - 200",
  "method": "GET",
  "path": "/user/123",
  "status_code": 200,
  "duration_ms": 12.5,
  "user_id": "123"
}
```

## Useful Kibana Searches

### Search by Log Level
```
level: ERROR
level: WARNING
level: INFO
```

### Search by Application
```
app: app1
app: app2
```

### Search by Status Code
```
status_code: 500
status_code: 200
```

### Search by Path
```
path: "/user/*"
path: "/error"
```

### Combine Searches
```
level: ERROR AND app: app1
status_code: 500 AND duration_ms > 1000
```

## Filebeat Configuration Explained

```yaml
filebeat.inputs:
  - type: log
    paths:
      - /var/log/app/*.log    # Watch these log files
    json.keys_under_root: true # Parse JSON logs

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  indices:
    - index: "app-logs-%{+yyyy.MM.dd}"  # Daily indices
```

## Lab Exercises

### Exercise 1: Log Level Analysis
1. Generate 100 random logs: `curl "http://localhost:5000/generate?count=100"`
2. In Kibana, create a pie chart showing distribution of log levels
3. Menu → Visualize Library → Create → Pie

### Exercise 2: Error Investigation
1. Trigger errors: `for i in {1..10}; do curl http://localhost:5000/error; done`
2. In Kibana, filter for `level: ERROR`
3. Examine the stack traces in the logs

### Exercise 3: Performance Analysis
1. Hit the slow endpoint multiple times:
   ```bash
   for i in {1..20}; do curl http://localhost:5000/slow & done; wait
   ```
2. In Kibana, search for `path: "/slow"`
3. Create a visualization showing average `duration_ms`

### Exercise 4: Cross-App Correlation
1. Generate logs from both apps
2. Search for a specific user across all apps
3. Use Kibana's timeline to see request flow

## Production Considerations

### Security (Disabled in Lab)
```yaml
# In production, enable security:
xpack.security.enabled: true
```

### Index Lifecycle Management
```
# Auto-delete old logs after 30 days
PUT _ilm/policy/logs-policy
{
  "policy": {
    "phases": {
      "delete": {
        "min_age": "30d",
        "actions": { "delete": {} }
      }
    }
  }
}
```

### Scaling
- Add more Elasticsearch nodes for high availability
- Use dedicated ingest nodes for heavy log volumes
- Consider Logstash for complex log transformations

## Troubleshooting

### Elasticsearch not starting
```bash
# Check logs
docker-compose logs elasticsearch

# Common fix: increase vm.max_map_count
sudo sysctl -w vm.max_map_count=262144
```

### Logs not appearing in Kibana
```bash
# Check Filebeat logs
docker-compose logs filebeat

# Check if indices exist
curl http://localhost:9200/_cat/indices
```

### Kibana shows "No data"
1. Wait a minute for data to be indexed
2. Check the correct index pattern (`app-logs-*`)
3. Adjust the time range in Kibana (top right)

## Clean Up

```bash
# Stop all containers
docker-compose down

# Remove all data (including logs)
docker-compose down -v
```

## Files Structure

```
logging/
├── docker-compose.yml   # Orchestrates all services
├── Dockerfile           # Flask app container
├── app.py               # Sample app with structured logging
├── filebeat.yml         # Filebeat configuration
└── README.md            # This file
```
