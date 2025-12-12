# API Gateway Demo

```
Client → API Gateway (nginx) → Services
```

---

## Option 1: Single Host (Local/Dev)

Everything runs on one machine.

```
┌─────────────────────────────────────┐
│            ONE HOST                 │
│  ┌─────────┐                        │
│  │ Gateway │ :5000                  │
│  └────┬────┘                        │
│       ├────────────┐                │
│       ↓            ↓                │
│  ┌────────┐   ┌────────┐            │
│  │  User  │   │ Order  │            │
│  │ :5001  │   │ :5002  │            │
│  └────────┘   └────────┘            │
└─────────────────────────────────────┘
```

### Run

```bash
docker compose up --build
```

### Test

```bash
curl http://localhost:5000/users
curl http://localhost:5000/orders
```

---

## Option 2: Two Hosts (Production)

Gateway + User on Host 1, Order on Host 2.
Use **keepalived** for gateway failover.

```
        ┌─────────────────┐
        │   Virtual IP    │ (keepalived)
        └────────┬────────┘
                 │
    ┌────────────┴────────────┐
    ↓                         ↓
┌─────────┐              ┌─────────┐
│ HOST 1  │              │ HOST 2  │
│         │              │         │
│ Gateway │◄────────────►│ Order   │
│ User    │   HTTP       │ Service │
└─────────┘              └─────────┘
```

### Host 1: Gateway + User Service

```bash
# docker-compose.host1.yml
docker compose -f docker-compose.host1.yml up -d
```

### Host 2: Order Service

```bash
# Set gateway URL to Host 1
export GATEWAY_URL=http://HOST1_IP

docker compose -f docker-compose.host2.yml up -d
```

### Keepalived (Optional)

If Host 1 gateway dies, failover to backup:

```
┌─────────┐     ┌─────────┐
│ HOST 1  │     │ HOST 2  │
│ nginx   │     │ nginx   │
│ MASTER  │     │ BACKUP  │
└────┬────┘     └────┬────┘
     │               │
     └───────┬───────┘
             │
      Virtual IP (VIP)
      Clients connect here
```

---

## Files

```
api-gateway-demo/
├── docker-compose.yml        # Single host (local)
├── docker-compose.host1.yml  # Multi host: Gateway + User
├── docker-compose.host2.yml  # Multi host: Order
├── user-service/
│   ├── app.py
│   └── Dockerfile
├── order-service/
│   ├── app.py
│   └── Dockerfile
└── api-gateway/
    ├── nginx.local.conf      # Single host config
    └── nginx.conf            # Multi host config (edit HOST2_IP)
```

---

## Test

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
