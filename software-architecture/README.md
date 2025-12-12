# Software Architecture Patterns

Learn **3-Tier Architecture** vs **Clean Architecture**.

## 3-Tier Architecture

```
┌──────────────────────────┐
│   PRESENTATION LAYER     │  ← Routes, API endpoints
├──────────────────────────┤
│     BUSINESS LAYER       │  ← Business logic, services
├──────────────────────────┤
│       DATA LAYER         │  ← Database access
└──────────────────────────┘

Dependency: Presentation → Business → Data
```

## Clean Architecture

```
┌─────────────────────────────────────────┐
│         INFRASTRUCTURE                  │  ← DB implementations
│   ┌─────────────────────────────────┐   │
│   │       APPLICATION               │   │  ← Use cases
│   │   ┌─────────────────────────┐   │   │
│   │   │       DOMAIN            │   │   │  ← Entities, interfaces
│   │   └─────────────────────────┘   │   │
│   └─────────────────────────────────┘   │
└─────────────────────────────────────────┘

Dependency: Outside → Inside (Dependency Inversion)
```

## Key Difference

| | 3-Tier | Clean Architecture |
|--|--------|-------------------|
| **Business depends on** | Concrete DB class | Abstract interface |
| **Swap database** | Must change business | Only change config |
| **Testing** | Need mock DB | Use fake implementation |

## Run Labs

```bash
# Three-Tier (port 5000)
cd three-tier && docker compose up --build

# Clean Architecture (port 5001)
cd clean-architecture && docker compose up --build
```

## Quick Comparison

```python
# 3-Tier: tight coupling
from data import user_repository  # Business imports concrete

# Clean: dependency inversion
def __init__(self, repo: UserRepository):  # Business uses interface
```

## When to Use

- **3-Tier:** Simple CRUD apps, prototypes, small teams
- **Clean:** Complex domain logic, long-term projects, large teams

## How Clean Architecture Layers Work Together

```
┌─────────────────────────────────────────────────────────────┐
│  PRESENTATION  │  HTTP routes, controllers (same in both)  │
├─────────────────────────────────────────────────────────────┤
│  APPLICATION   │  WHY - Business logic, validation         │
│                │  Calls domain interfaces                   │
├─────────────────────────────────────────────────────────────┤
│  DOMAIN        │  WHAT - Defines interfaces/contracts      │
│                │  "I need a UserRepository"                │
├─────────────────────────────────────────────────────────────┤
│  INFRASTRUCTURE│  HOW - Implements interfaces              │
│                │  SQLite, PostgreSQL, MongoDB (SWAPPABLE)  │
└─────────────────────────────────────────────────────────────┘
```

```python
# 1. Domain says WHAT it needs
class UserRepository(ABC):
    def create(self, name, email): pass

# 2. Application says WHY (business rules)
class UserService:
    def register(self, name, email):
        if not email:
            raise ValueError("Email required")
        return self.repo.create(name, email)

# 3. Infrastructure says HOW
class SQLiteUserRepository(UserRepository):   # Option A
class PostgresUserRepository(UserRepository): # Option B

# 4. Swap freely - business logic untouched
repo = PostgresUserRepository()  # Just change this line
service = UserService(repo)      # Service doesn't care
```

## What Changes When You Swap Database?

| Layer | Changes? |
|-------|----------|
| Presentation | No |
| Application | No |
| Domain | No |
| Infrastructure | **Yes (only here)** |
