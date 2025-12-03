# Load Balancer Lab (Nginx)

Distribute traffic across multiple backend servers using round-robin.

```bash
docker compose up --build
chmod +x test.sh && ./test.sh
```

**Endpoints:**
- `GET /` - Returns which backend handled the request
- `GET /heavy` - Simulate heavy processing

**Test:** Send multiple requests to see round-robin distribution.
