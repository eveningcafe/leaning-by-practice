# Cache Labs (Redis)

## Lab 1.1: DB Caching - Reduce Database Load

Demonstrates how Redis caching reduces the number of database queries.

### How It Works

```
Request → Check Redis → Found? → Return cached data (no DB query)
                      ↓
                   Not found? → Query MySQL → Store in Redis → Return data
```

```python
cached = redis_client.get(cache_key)    # 1. Check Redis first
if cached:                              # 2. Cache HIT → return from Redis
    return cached
result = query_from_db()                # 3. Cache MISS → query database
redis_client.setex(cache_key, 60, ...)  # 4. Store in Redis for 60s
return result
```

### Run the Lab

```bash
cd db-cache
docker compose up --build
```

Wait ~10 seconds for initialization, then in another terminal:

```bash
chmod +x test.sh && ./test.sh
```

Or test manually:

```bash
curl http://localhost:5000/             # API documentation
curl http://localhost:5000/stats/reset  # Reset counters
curl http://localhost:5000/products     # First call → hits DB
curl http://localhost:5000/products     # Second call → hits Redis cache
curl http://localhost:5000/stats        # See: 1 db_hit, 1 cache_hit
```

### Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | API documentation |
| `GET /products` | Get products WITH caching (reduces DB load) |
| `GET /products/no-cache` | Get products WITHOUT caching (always hits DB) |
| `GET /stats` | View cache effectiveness (db_hits, cache_hits, hit rate) |
| `GET /stats/reset` | Reset statistics and clear cache |

### Expected Result

```
With caching:    10 requests = 1 DB query + 9 cache hits (90% reduction)
Without caching: 10 requests = 10 DB queries
```

### Demo 2: Cache Invalidation

What happens when data is updated? Cache can become stale!

#### How It Works

```
READ:   Request → Check Redis → Found? → Return cached data
                             ↓
                          Not found? → Query DB → Cache it → Return

UPDATE (without invalidation):
        Update DB → Cache still has OLD data → Stale until TTL expires!

UPDATE (with invalidation):
        Update DB → Delete cache → Next read gets fresh data
```

```python
# Without invalidation - causes stale data
def add_points(customer_id):
    cur.execute('UPDATE customers SET points = points + 50 ...')
    # Cache NOT deleted - /customers returns old value!

# With invalidation - always fresh
def add_points_invalidate(customer_id):
    cur.execute('UPDATE customers SET points = points + 50 ...')
    redis_client.delete('customers:all')  # Clear cache!
```

#### Endpoints

| Endpoint | Description |
|----------|-------------|
| `/customers` | Get customers (cached 10s TTL) |
| `/customers/1/add-points` | Update WITHOUT invalidation (stale!) |
| `/customers/1/add-points-invalidate` | Update WITH invalidation (fresh) |

#### Try This

```bash
curl http://localhost:5000/customers                        # Alice: 100 pts
curl http://localhost:5000/customers/1/add-points           # DB → 150 pts
curl http://localhost:5000/customers                        # Still 100! (stale)
# Wait 10s for TTL to expire, OR:
curl http://localhost:5000/customers/1/add-points-invalidate
curl http://localhost:5000/customers                        # Now shows fresh data
```

---

## Lab 1.2: Session Sharing

Share session across multiple app instances using Redis.

### How It Works

```
Without Redis:  App1 stores session locally → App2 doesn't know about it
                User logs in on App1 → Redirected to App2 → "Not logged in!"

With Redis:     All apps share session storage
                User logs in on App1 → Session stored in Redis → App2 can read it
```

```python
# Session stored in Redis, not local memory
redis_client.setex(f'session:{session_id}', 3600, json.dumps(user_data))

# Any app instance can read the session
session_data = redis_client.get(f'session:{session_id}')
```

### Run the Lab

```bash
cd session
docker compose up --build
```

Then in another terminal:

```bash
chmod +x test.sh && ./test.sh
```

### Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /login/<username>` | Login on any app |
| `GET /profile` | View profile (works on all apps with same session) |
| `GET /logout` | Logout |

### Test Manually

```bash
# 1. Login on App1 (port 5001) - save the cookie
curl -c cookies.txt http://localhost:5001/login/alice
# → Logged in as alice on app1

# 2. Access profile on App2 (port 5002) - using same cookie
curl -b cookies.txt http://localhost:5002/profile
# → Shows alice's profile (session shared via Redis!)

# 3. Access profile on App3 (port 5003) - still works
curl -b cookies.txt http://localhost:5003/profile
# → Shows alice's profile

# 4. Logout from any app
curl -b cookies.txt http://localhost:5002/logout
# → Session deleted from Redis

# 5. Try profile again - session gone everywhere
curl -b cookies.txt http://localhost:5001/profile
# → Not logged in
```

### Key Takeaway

```
Without Redis: Each app has its own session → User must login again on each
With Redis:    Sessions shared across all apps → Login once, works everywhere
```

---

## Lab 1.3: Distributed Lock - Prevent Race Conditions

Prevent race conditions when multiple app instances access shared resources.

### The Problem

```
Without Lock:
  App1: Read stock (100) ──────────────────→ Decrement → stock = 99
  App2:      Read stock (100) ─────────────→ Decrement → stock = 99  (WRONG!)
  App3:           Read stock (100) ────────→ Decrement → stock = 99  (WRONG!)

  Result: 3 purchases but stock only decreased by 1! (Overselling)

With Lock:
  App1: Acquire lock → Read (100) → Decrement (99) → Release lock
  App2:                 [waiting for lock...] → Acquire → Read (99) → Decrement (98) → Release
  App3:                                          [waiting...] → Acquire → Read (98) → Decrement (97) → Release

  Result: 3 purchases, stock correctly decreased by 3
```

### Without Lock (Race Condition)

```python
# Non-atomic read-modify-write - causes race condition!
stock = redis_client.get('product:stock')   # App1 reads 100, App2 reads 100
time.sleep(0.1)                              # Both processing...
redis_client.set('product:stock', stock - 1) # Both write 99! (should be 98)
```

### How It Works

```python
# Acquire lock using SET NX (Set if Not eXists)
lock_id = uuid.uuid4()
acquired = redis_client.set(f'lock:{name}', lock_id, nx=True, ex=10)

if acquired:
    try:
        # CRITICAL SECTION - only one process can be here
        stock = redis_client.get('product:stock')
        redis_client.decr('product:stock')
    finally:
        # Release lock (only if we own it)
        release_lock(name, lock_id)
```

### Run the Lab

```bash
cd distributed-lock
docker compose up --build
```

Wait for startup, then in another terminal:

```bash
chmod +x test.sh && ./test.sh
```

### Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | API documentation |
| `GET /buy/no-lock` | Purchase WITHOUT lock (race condition!) |
| `GET /buy/with-lock` | Purchase WITH lock (safe) |
| `GET /buy/with-lock-retry` | Purchase WITH lock + retry (safe + resilient) |
| `GET /stock` | Check current stock |
| `GET /stock/reset` | Reset stock to 100 |
| `GET /stats` | View purchase stats and race condition count |

### Test Manually

```bash
# 1. Reset stock
curl http://localhost:5001/stock/reset

# 2. Send concurrent requests WITHOUT lock (causes race conditions)
for i in {1..10}; do curl -s http://localhost:500$((1 + i % 3))/buy/no-lock & done; wait

# 3. Check stats - race_conditions_detected > 0 means overselling!
curl http://localhost:5001/stats | jq .

# 4. Reset and try WITH lock
curl http://localhost:5001/stock/reset
for i in {1..10}; do curl -s http://localhost:500$((1 + i % 3))/buy/with-lock-retry & done; wait

# 5. Check stats - no race conditions, stock is accurate
curl http://localhost:5001/stats | jq .
```

### Expected Result

```
Without lock: 20 purchases → stock mismatch, race conditions detected
With lock:    20 purchases → stock = 80, no race conditions
```

### Key Takeaway

```
Without Lock: Multiple apps can read/write simultaneously → Data corruption
With Lock:    Only one app can access critical section → Data integrity
```
