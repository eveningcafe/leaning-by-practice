# Microservices Example

Separate services, separate databases.

```
┌─────────────┐      ┌─────────────┐
│ User Service│      │Order Service│
│    :5001    │      │    :5002    │
│    VPS 1    │      │    VPS 2    │
└──────┬──────┘      └──────┬──────┘
     [DB1]               [DB2]
```

## The Problem: How Do Services Find Each Other?

```
Order service needs to call User service, but:

- What IP is User service running on?
- What if User service restarts with new IP?
- What if there are multiple User service instances?
```

**Hardcoding IPs doesn't scale:**
```python
USER_SERVICE = "http://192.168.1.100:5001"  # What if this changes?
```

---

## Solution 1: API Gateway (Simple)

Gateway knows all service locations. All traffic goes through it.

```
        ┌─────────────┐
        │ API Gateway │ ← Knows all IPs
        │    :80      │
        └──────┬──────┘
               │
    ┌──────────┴──────────┐
    ↓                     ↓
┌────────┐           ┌────────┐
│  User  │           │ Order  │
│ :5001  │           │ :5002  │
└────────┘           └────────┘

Order calls: GET http://gateway/users/1
Gateway routes to → User service
```

**Pros:**
- Simple to implement
- Centralized routing
- One place to update IPs

**Cons:**
- Single point of failure
- Extra network hop
- Gateway must know all services

**Example:**
```python
# order-service calls via gateway
GATEWAY = os.getenv("GATEWAY_URL", "http://gateway")
resp = requests.get(f"{GATEWAY}/users/{user_id}")
```

---

## Solution 2: Service Discovery (Advanced)

Services register themselves. Others query to find them.

```
┌──────────────────┐
│ Service Registry │ ← Consul, etcd
│ (knows who's up) │
└────────┬─────────┘
         │
    ┌────┴────┐
    ↓         ↓
┌────────┐ ┌────────┐
│  User  │ │ Order  │
│register│ │  query │
└────────┘ └────────┘

1. User service starts → registers with registry
2. Order needs User → asks registry "where is User?"
3. Registry returns → "User is at 192.168.1.100:5001"
4. Order calls User directly
```

**Pros:**
- Dynamic (handles IP changes)
- No single point of failure
- Direct service-to-service (fast)

**Cons:**
- More complex setup
- Need to run registry (Consul, Eureka)
- Services need discovery client

**Tools:**
| Tool | Used By |
|------|---------|
| Consul | HashiCorp |
| etcd | Kubernetes |
| Kubernetes DNS | K8s built-in |

**Example (with Consul):**
```python
# order-service discovers user-service
import consul
c = consul.Consul()
_, services = c.health.service('user-service', passing=True)
user_host = services[0]['Service']['Address']
user_port = services[0]['Service']['Port']
resp = requests.get(f"http://{user_host}:{user_port}/users/{user_id}")
```

---

## Comparison

| | API Gateway | Service Discovery |
|--|-------------|-------------------|
| **Complexity** | Simple | Complex |
| **Setup** | Just Nginx | Need Consul/Eureka |
| **Speed** | Extra hop | Direct calls |
| **Failure** | Gateway down = all down | Registry down = no new discovery |
| **Best for** | Small systems | Large systems |

---

## This Demo: Two Implementations

```
microservices/
├── README.md
├── api-gateway-demo/      # Solution 1: API Gateway
│   ├── user-service/
│   ├── order-service/
│   ├── api-gateway/
│   └── docker-compose.yml
└── service-discovery/     # Solution 2: Consul
    ├── user-service/
    ├── order-service/
    └── docker-compose.yml  (includes Consul)
```

---

## Solution 1: API Gateway Flow

```
Client                Gateway:80              user:5001    order:5002
  │                      │                       │            │
  │── GET /users ───────►│                       │            │
  │                      │── proxy to ──────────►│            │
  │                      │◄── response ──────────│            │
  │◄── response ─────────│                       │            │
  │                      │                       │            │
  │── POST /orders ─────►│                       │            │
  │                      │── proxy to ───────────────────────►│
  │                      │                       │            │
  │                      │   (order needs user)  │            │
  │                      │◄── GET /users/1 ──────────────────│
  │                      │── proxy to ──────────►│            │
  │                      │◄── user data ─────────│            │
  │                      │── user data ─────────────────────►│
  │                      │◄── order created ─────────────────│
  │◄── response ─────────│                       │            │
```

### Run API Gateway Demo

```bash
cd api-gateway-demo
docker compose up --build
```

### Test

```bash
# Create user
curl -X POST http://localhost/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice"}'

# Create order (order → gateway → user)
curl -X POST http://localhost/orders \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "item": "Book"}'
```

---

## Solution 2: Service Discovery Flow

```
                    ┌────────────────┐
                    │     Consul     │
                    │   (registry)   │
                    └───────┬────────┘
                            │
           ┌────────────────┼────────────────┐
           │ register       │ register       │ discover
           │                │                │
     ┌─────▼─────┐    ┌─────▼─────┐    ┌─────▼─────┐
     │   User    │    │   Order   │    │   Order   │
     │  Service  │◄───│  Service  │────│  calls    │
     │   :5001   │    │   :5002   │    │  directly │
     └───────────┘    └───────────┘    └───────────┘
                            │
                      1. Register with Consul
                      2. Query Consul for user-service
                      3. Get IP:port
                      4. Call user-service directly
```

### Run Service Discovery Demo

```bash
cd service-discovery
docker compose up --build
```

### Test

```bash
# Check Consul UI
open http://localhost:8500

# Create user
curl -X POST http://localhost:5001/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice"}'

# Create order (order discovers user via Consul)
curl -X POST http://localhost:5002/orders \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "item": "Book"}'
```
