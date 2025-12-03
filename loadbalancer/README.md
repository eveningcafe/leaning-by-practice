# Load Balancer Lab (Nginx)

Distribute traffic across multiple backend servers using round-robin.

## How It Works

```
Without Load Balancer:
        Client → Single Server → Overloaded!

With Load Balancer (Round-Robin):
        Client → Nginx → Backend1 (request 1)
                      → Backend2 (request 2)
                      → Backend3 (request 3)
                      → Backend1 (request 4) ...
```

```nginx
# nginx.conf
upstream backends {
    # Round-robin by default (rotates through servers)
    server backend1:5000;
    server backend2:5000;
    server backend3:5000;
}

server {
    listen 80;
    location / {
        proxy_pass http://backends;  # Nginx distributes requests
    }
}
```

## Run the Lab

```bash
cd loadbalancer
docker compose up --build
```

Then in another terminal:

```bash
chmod +x test.sh && ./test.sh
```

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Returns which backend handled the request |
| `GET /heavy` | Simulate heavy processing (1s delay) |
| `GET /health` | Health check endpoint |

## Test Manually

```bash
# 1. Send multiple requests - see round-robin distribution
curl http://localhost:80/
# → {"server": "backend1", "request_count": 1}

curl http://localhost:80/
# → {"server": "backend2", "request_count": 1}

curl http://localhost:80/
# → {"server": "backend3", "request_count": 1}

curl http://localhost:80/
# → {"server": "backend1", "request_count": 2}  # Back to backend1

# 2. Send 10 requests and see distribution
for i in {1..10}; do curl -s http://localhost:80/ | jq -r '.server'; done
# → backend1, backend2, backend3, backend1, backend2...

# 3. Test heavy endpoint - requests distributed even under load
curl http://localhost:80/heavy
# → {"server": "backend1", "task": "heavy processing done"}

# 4. Health check
curl http://localhost:80/health
# → {"status": "ok", "server": "backend2"}
```

## Key Takeaway

```
Without LB: 100 requests → 1 server handles all → Slow, single point of failure
With LB:    100 requests → ~33 each server → Fast, fault tolerant
```
