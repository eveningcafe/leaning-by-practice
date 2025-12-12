# Service Discovery with Consul

Services register and discover each other dynamically. No gateway needed.

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

---

## Option 1: Single Host (Local/Dev)

Everything runs on one machine.

```
┌─────────────────────────────────────┐
│            ONE HOST                 │
│  ┌──────────┐                       │
│  │  Consul  │ :8500                 │
│  └────┬─────┘                       │
│       │ register + discover         │
│  ┌────┴────┐                        │
│  ↓         ↓                        │
│ ┌────┐   ┌─────┐                    │
│ │User│   │Order│                    │
│ └────┘   └─────┘                    │
└─────────────────────────────────────┘
```

### Run

```bash
docker compose up --build
```

### Test

```bash
# Consul UI
open http://localhost:8500

# Create user + order
curl -X POST http://localhost:5001/users -H "Content-Type: application/json" -d '{"name": "Alice"}'
curl -X POST http://localhost:5002/orders -H "Content-Type: application/json" -d '{"user_id": 1, "item": "Book"}'
```

---

## Option 2: Multi Host (Production)

Consul cluster across hosts. Services register to local Consul agent.

```
┌─────────────────┐     ┌─────────────────┐
│     HOST 1      │     │     HOST 2      │
│                 │     │                 │
│ ┌─────────────┐ │     │ ┌─────────────┐ │
│ │Consul Agent │◄┼─────┼─┤Consul Agent │ │
│ └──────┬──────┘ │     │ └──────┬──────┘ │
│        │        │     │        │        │
│ ┌──────▼──────┐ │     │ ┌──────▼──────┐ │
│ │ User Service│ │     │ │Order Service│ │
│ └─────────────┘ │     │ └─────────────┘ │
└─────────────────┘     └─────────────────┘

Order discovers User via Consul → calls User directly
```

### Host 1: Consul + User

```bash
docker compose -f docker-compose.host1.yml up -d
```

### Host 2: Consul + Order

```bash
# Set Consul join address
export CONSUL_JOIN=HOST1_IP

docker compose -f docker-compose.host2.yml up -d
```

---

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

# 3. Call directly (no gateway!)
resp = requests.get(f"{user_url}/users/1")
```

---

## Files

```
service-discovery/
├── docker-compose.yml         # Single host
├── docker-compose.host1.yml   # Multi host: Consul + User
├── docker-compose.host2.yml   # Multi host: Consul + Order
├── user-service/
│   ├── app.py                 # Registers with Consul
│   └── Dockerfile
└── order-service/
    ├── app.py                 # Discovers via Consul
    └── Dockerfile
```

---

## Key Difference from API Gateway

```
API Gateway:       order → gateway → user (extra hop)
Service Discovery: order → consul (query) → user (direct, faster)
```
