# System Design Patterns

Learn **Monolith** vs **Microservices**.

## Monolith

```
┌─────────────────────────────────┐
│        ONE APPLICATION          │
│   ┌──────┐      ┌──────┐       │
│   │ User │      │ Order│       │
│   └──────┘      └──────┘       │
│         ONE DATABASE            │
└─────────────────────────────────┘
        Single deployment
```

## Microservices

```
┌───────────┐      ┌───────────┐
│   User    │      │   Order   │
│  Service  │ ──── │  Service  │
│   :5001   │ HTTP │   :5002   │
└─────┬─────┘      └─────┬─────┘
    [DB1]              [DB2]

  Separate deployments
```

## Key Difference

| | Monolith | Microservices |
|--|----------|---------------|
| **Deployment** | One unit | Many units |
| **Database** | Shared | Separate per service |
| **Scaling** | Scale everything | Scale what you need |
| **Complexity** | Simple | Complex |
| **Failure** | All or nothing | Partial failure |

## Run Labs

```bash
# Monolith (port 5000)
cd monolith && docker compose up --build

# Microservices (ports 5001, 5002)
cd microservices && docker compose up --build
```

## When to Use

- **Monolith:** Small team, new project, fast iteration
- **Microservices:** Large team, need independent scaling

## Common Mistake

```
Start monolith → Grow → Split when needed
```

Don't start with microservices too early.
