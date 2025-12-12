# Clean Architecture Example

## History

**Created by:** Robert C. Martin (Uncle Bob) in 2012

**Blog post:** "The Clean Architecture" (August 2012)

**Book:** "Clean Architecture: A Craftsman's Guide to Software Structure and Design" (2017)

**Core idea:** Separate business rules from frameworks/databases so your code is testable, maintainable, and framework-independent.

---

## Structure

```
domain/          →  application/     →  infrastructure/
  interfaces.py      user_service.py     sqlite_repository.py
       ↑                  ↑               postgres_repository.py
       └──────────────────┘ (depends on interface, not concrete)
```

## Run

### Option 1: SQLite (default)

```bash
docker compose up --build
```

### Option 2: PostgreSQL (swap infrastructure)

```bash
docker compose -f docker-compose.postgres.yml up --build
```

**Same business logic, different database!**

## Test

```bash
# List users
curl http://localhost:5001/users

# Create user
curl -X POST http://localhost:5001/users \
  -H "Content-Type: application/json" \
  -d '{"name": "John", "email": "john@test.com"}'

# Get user
curl http://localhost:5001/users/1

# Delete user
curl -X DELETE http://localhost:5001/users/1
```

## Key Difference: Dependency Inversion

```python
# app.py (composition root)
repo = SQLiteUserRepository()      # Concrete implementation
service = UserService(repo)         # Inject via constructor

# application/user_service.py
class UserService:
    def __init__(self, repo: UserRepository):  # Depends on interface!
        self.repo = repo
```

**Benefit:** To swap SQLite for PostgreSQL, only change `app.py`:
```python
repo = PostgresUserRepository()  # No change to UserService!
```

## Files

```
clean-architecture/
├── docker-compose.yml           # SQLite version
├── docker-compose.postgres.yml  # PostgreSQL version
├── app.py                       # Uses SQLite
├── app.postgres.py              # Uses PostgreSQL
├── Dockerfile                   # SQLite
├── Dockerfile.postgres          # PostgreSQL
├── domain/
│   └── interfaces.py            # Repository interface
├── application/
│   └── user_service.py          # Business logic (unchanged!)
├── infrastructure/
│   ├── sqlite_repository.py     # SQLite implementation
│   └── postgres_repository.py   # PostgreSQL implementation
└── presentation/
    └── routes.py                # HTTP handlers
```

## How to Swap Database

Add new implementation in `infrastructure/`, then change `app.py`:

```python
# app.py (SQLite)
from infrastructure.sqlite_repository import SQLiteUserRepository
repo = SQLiteUserRepository()

# app.postgres.py (PostgreSQL)
from infrastructure.postgres_repository import PostgresUserRepository
repo = PostgresUserRepository(host="db", port=5432, ...)
```

**UserService stays exactly the same!**

## What Can Be Swapped?

Not just database - **anything external**:

| Type | Examples |
|------|----------|
| Database | SQLite → PostgreSQL → MongoDB |
| Cache | Redis → Memcached |
| Email | SMTP → SendGrid → AWS SES |
| Storage | Local → S3 → Google Cloud |
| Payment | Stripe → PayPal |

## Why These Layer Names?

| Layer | Meaning | Example |
|-------|---------|---------|
| **Domain** | WHAT - Business rules (exist without code) | "Email must be unique" |
| **Application** | WHY - Use cases (actions users perform) | "Register user" |
| **Infrastructure** | HOW - Technical details (replaceable) | SQLite, Flask, Redis |
