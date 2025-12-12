# Monolith Example

All modules in one application, one database.

```
┌─────────────────────────────┐
│          app.py             │
│   [User]       [Order]      │
│         ↓   ↓               │
│       [SQLite]              │
└─────────────────────────────┘
```

## Run

```bash
docker compose up --build
```

## Test

```bash
# Create user
curl -X POST http://localhost:5000/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice"}'

# Create order (direct DB check for user)
curl -X POST http://localhost:5000/orders \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "item": "Book"}'

# List all
curl http://localhost:5000/users
curl http://localhost:5000/orders
```

## Pros

- Simple deployment
- Easy to develop
- No network calls between modules

## Cons

- Must deploy everything together
- Can't scale modules independently
