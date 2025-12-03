# Cache Labs (Redis)

## Lab 1.1: DB Caching
Cache database queries to reduce load.

```bash
cd db-cache
docker compose up --build
chmod +x test.sh && ./test.sh
```

**Endpoints:**
- `GET /users/no-cache` - Direct DB query (slow)
- `GET /users/cached` - Cached query (fast)
- `GET /clear-cache` - Clear cache

---

## Lab 1.2: Session Sharing
Share session across multiple app instances.

```bash
cd session
docker compose up --build
chmod +x test.sh && ./test.sh
```

**Endpoints:**
- `GET /login/<username>` - Login on any app
- `GET /profile` - View profile (works on all apps with same session)
- `GET /logout` - Logout

**Test:** Login on app1 (port 5001), access profile from app2 (port 5002) or app3 (port 5003).
