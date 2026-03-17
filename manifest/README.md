# Package Manifest: SystemD vs Docker

## Why Package Management?

Software needs a way to describe:
- What files to install and where
- When and how to run
- What dependencies are required
- How to manage lifecycle (start, stop, restart)
- Resource limits and permissions

This led to package managers (apt, yum) and service managers (systemd) working together to deploy applications. Later, containers emerged as an alternative approach using namespaces for isolation.

## Key Questions Package Systems Must Answer

1. **When will the program run?** (startup, on-demand, scheduled?)
2. **What to prepare before running?** (dependencies, environment, permissions)
3. **What happens after program stops?** (restart, cleanup, logs)
4. **What are the dependencies?** (libraries, other services)
5. **How to limit resources?** (CPU, memory, disk)
6. **How to cleanup?** (remove files, stop processes, free ports)

## Building a Simple Python Web App - Two Methods

### Our App
A Python web application that counts visits using Redis as a cache. The app:
- Serves HTTP requests on port 5000
- Uses Flask web framework
- Depends on Redis for storing visit counter
- Needs both Python runtime and Redis service to function

## Method 1: SystemD + DEB Package

### Package Structure (hello-app.deb)
```
DEBIAN/
  control         # Package metadata
  postinst        # Setup script after install
  prerm           # Cleanup before removal
  
usr/
  local/
    bin/
      hello-app   # Our Python app
      
etc/
  systemd/
    system/
      hello-app.service   # Service definition
```

### control file (Package Manifest)
```
Package: hello-app
Version: 1.0
Architecture: all
Depends: python3, python3-flask, redis-server
Maintainer: Dev Team
Description: Simple web counter app
```

### hello-app.service (SystemD Manifest)
```ini
[Unit]
Description=Hello Web App
After=network.target redis.service
Requires=redis.service

[Service]
Type=simple
User=www-data
Environment="REDIS_HOST=localhost"
ExecStart=/usr/bin/python3 /usr/local/bin/hello-app
Restart=on-failure
# Resource limits
CPUQuota=50%
MemoryLimit=256M

[Install]
WantedBy=multi-user.target
```

### How SystemD Answers the Questions:
- **When runs:** After network.target and redis.service (dependencies)
  - Targets = groups of services that start together (multi-user.target = normal system boot)
  - Common targets: basic.target → multi-user.target → graphical.target
  - WantedBy=multi-user.target means "start when system reaches multi-user mode"
- **Preparation:** DEB installs Python, Flask, Redis system-wide
- **After stop:** Restart=on-failure handles crashes
- **Dependencies:** Shared with system (python3, redis-server)
- **Resources:** CPUQuota and MemoryLimit in service file
- **Cleanup:** `apt remove hello-app` runs prerm script


## Method 2: Docker Container

### Dockerfile (Container Manifest)
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Dependencies in container
RUN pip install flask redis

# App files
COPY hello.py .

# Runtime config
ENV REDIS_HOST=redis
EXPOSE 5000

# Resource hints (enforced at runtime)
# docker run --memory="256m" --cpus="0.5"

CMD ["python", "hello.py"]
```

### docker-compose.yml (Orchestration Manifest)
```yaml
version: '3'
services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - REDIS_HOST=redis
    depends_on:
      - redis
    restart: unless-stopped
    # Resource limits
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
          
  redis:
    image: redis:alpine
```

### How Docker Answers the Questions:
- **When runs:** Container starts when docker run/compose up
- **Preparation:** Everything bundled in image layers
- **After stop:** restart: unless-stopped policy
- **Dependencies:** Isolated inside container (no conflicts!)
- **Resources:** Cgroups enforce limits per container
- **Cleanup:** `docker rm` removes container and its filesystem

## Key Differences

| Aspect | SystemD/DEB | Docker |
|--------|------------|--------|
| **Dependencies** | System-wide (shared) | Per-container (isolated) |
| **File location** | Spread across filesystem | Layered image filesystem |
| **Updates** | In-place, affects all | New image, blue-green deploy |
| **Resource isolation** | Process-level | Namespace + cgroup isolation |
| **Portability** | Linux distro specific | Runs anywhere with Docker |
| **Disk usage** | Shared libraries (less) | Each container has copies (more) |


## When to Use Which

**Use SystemD when:**
- System services (network managers, device drivers)
- Resource critical (every MB matters)
- Direct hardware access needed
- Single server, simple deployments

**Use Docker when:**
- Multiple environments (dev/staging/prod)
- Microservices architecture
- Team collaboration
- Need isolation between apps
- Cloud deployments

Both methods solve the same problems differently. SystemD integrates with the OS, while Docker isolates from it.