# Three-Tier Architecture Example

```
presentation/  →  business/  →  data/
   routes.py      user_service.py   user_repository.py
```

## Run

```bash
docker compose up --build
```

## Test

```bash
# List users
curl http://localhost:5000/users

# Create user
curl -X POST http://localhost:5000/users \
  -H "Content-Type: application/json" \
  -d '{"name": "John", "email": "john@test.com"}'

# Get user
curl http://localhost:5000/users/1

# Delete user
curl -X DELETE http://localhost:5000/users/1
```

## Problem with 3-Tier

Business layer directly imports data layer:

```python
# business/user_service.py
from data import user_repository  # Tight coupling!
```

If you want to swap SQLite for PostgreSQL, you must modify business layer.
