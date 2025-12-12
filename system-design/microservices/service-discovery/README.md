# Service Discovery with Consul

Services register and discover each other dynamically.

```
┌────────────────┐
│     Consul     │ :8500 (UI)
│   (registry)   │
└───────┬────────┘
        │
   ┌────┴────┐
   │register │ + discover
   ↓         ↓
┌────────┐ ┌────────┐
│  User  │ │ Order  │
│ :5001  │ │ :5002  │
└────────┘ └────────┘
```

## How It Works

```python
# 1. Service registers on startup
c.agent.service.register(
    name="user-service",
    address=get_ip(),
    port=5001
)

# 2. Other service discovers it
_, services = c.health.service("user-service", passing=True)
user_url = f"http://{services[0]['Service']['Address']}:{services[0]['Service']['Port']}"

# 3. Call directly (no gateway)
resp = requests.get(f"{user_url}/users/1")
```

## Run

```bash
docker compose up --build
```

## Test

```bash
# Check Consul UI
open http://localhost:8500

# Check registered services
curl http://localhost:8500/v1/agent/services | jq

# Create user
curl -X POST http://localhost:5001/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice"}'

# Create order (order discovers user via Consul)
curl -X POST http://localhost:5002/orders \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "item": "Book"}'

# See discovered URL in response
curl http://localhost:5002/
```

## Key Difference from API Gateway

```
API Gateway:     order → gateway → user (extra hop)
Service Discovery: order → consul (query) → user (direct)
```
