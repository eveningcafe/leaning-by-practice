# Git CD Lab (Deploy to VPS via SSH + Docker)

## References

- [GitHub Actions: Deploy via SSH](https://docs.github.com/en/actions/deployment)
- [appleboy/ssh-action](https://github.com/appleboy/ssh-action)

---

## What is CD?

```
CI passes → Auto deploy to VPS
                    ↓
┌──────────────────────────────────┐
│           Your VPS               │
│                                  │
│   docker pull → docker run       │
│                                  │
└──────────────────────────────────┘
```

---

## Project Structure

```
myapp/
├── .github/
│   └── workflows/
│       └── cd.yml        # GitHub Actions CD
├── app.py                # Simple Flask app
├── Dockerfile
└── docker-compose.yml
```

---

## Step 1: Create Simple App

```bash
mkdir myapp && cd myapp

# app.py
cat > app.py << 'EOF'
from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello from CD! Version 1.0"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
EOF
```

---

## Step 2: Create Dockerfile

```bash
cat > Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /app
RUN pip install flask
COPY app.py .
CMD ["python", "app.py"]
EOF
```

---

## Step 3: Create docker-compose.yml

```bash
cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  app:
    build: .
    ports:
      - "5000:5000"
    restart: unless-stopped
EOF
```

---

## Step 4: Setup VPS

On your VPS (Ubuntu):

```bash
# Install Docker (if not installed)
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Create deploy directory
mkdir -p ~/myapp
```

---

## Step 5: Setup SSH Key for GitHub Actions

On your local machine:

```bash
# Generate SSH key (no passphrase)
ssh-keygen -t ed25519 -f ~/.ssh/github_actions -N ""

# Copy public key to VPS
ssh-copy-id -i ~/.ssh/github_actions.pub user@YOUR_VPS_IP

# View private key (need this for GitHub Secret)
cat ~/.ssh/github_actions
```

---

## Step 6: Add Secrets to GitHub

Go to: `GitHub Repo → Settings → Secrets and variables → Actions`

Add these secrets:

| Secret Name | Value |
|-------------|-------|
| `VPS_HOST` | Your VPS IP (e.g., 192.168.1.100) |
| `VPS_USER` | SSH username (e.g., ubuntu) |
| `VPS_SSH_KEY` | Content of `~/.ssh/github_actions` (private key) |

---

## Step 7: Create CD Workflow

```bash
mkdir -p .github/workflows

cat > .github/workflows/cd.yml << 'EOF'
name: CD

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Copy files to VPS
        uses: appleboy/scp-action@v0.1.7
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.VPS_SSH_KEY }}
          source: "app.py,Dockerfile,docker-compose.yml"
          target: "~/myapp"

      - name: Deploy on VPS
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.VPS_SSH_KEY }}
          script: |
            cd ~/myapp
            docker compose down
            docker compose up -d --build
            docker ps
EOF
```

---

## Step 8: Push and Deploy

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/eveningcafe/myapp.git
git push -u origin main
```

---

## What Happens

```
1. Push to main
        ↓
2. GitHub Actions starts
        ↓
3. Copy files to VPS via SCP
        ↓
4. SSH into VPS
        ↓
5. docker compose down (stop old)
        ↓
6. docker compose up --build (start new)
        ↓
7. App running at http://YOUR_VPS_IP:5000
```

---

## Test Deployment

```bash
# After push, check your app
curl http://YOUR_VPS_IP:5000
# Hello from CD! Version 1.0

# Update app.py
echo 'return "Hello from CD! Version 2.0"' # edit app.py

git commit -am "Update to v2"
git push

# Wait for Actions to complete, then:
curl http://YOUR_VPS_IP:5000
# Hello from CD! Version 2.0
```

---

## View Logs

On VPS:

```bash
cd ~/myapp
docker compose logs -f
```

---

## Alternative: Use Docker Hub

Instead of copying files, build and push to Docker Hub:

```yaml
name: CD via Docker Hub

on:
  push:
    branches: [main]

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Login to Docker Hub
        run: echo "${{ secrets.DOCKER_PASSWORD }}" | docker login -u "${{ secrets.DOCKER_USERNAME }}" --password-stdin

      - name: Build and push
        run: |
          docker build -t eveningcafe/myapp:latest .
          docker push eveningcafe/myapp:latest

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    steps:
      - name: Deploy on VPS
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.VPS_SSH_KEY }}
          script: |
            docker pull eveningcafe/myapp:latest
            docker stop myapp || true
            docker rm myapp || true
            docker run -d --name myapp -p 5000:5000 eveningcafe/myapp:latest
```

---

## Diagram

```
┌─────────────┐     push      ┌─────────────────┐
│   Local     │ ────────────► │     GitHub      │
│   Code      │               │                 │
└─────────────┘               │  Actions runs:  │
                              │  1. Copy files  │
                              │  2. SSH deploy  │
                              └────────┬────────┘
                                       │
                                       ▼ SSH
                              ┌─────────────────┐
                              │      VPS        │
                              │                 │
                              │  docker compose │
                              │  up --build     │
                              │                 │
                              │  App running    │
                              │  on port 5000   │
                              └─────────────────┘
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| SSH connection failed | Check VPS_HOST, VPS_USER, VPS_SSH_KEY secrets |
| Permission denied | Ensure SSH key is added to VPS `~/.ssh/authorized_keys` |
| Docker command not found | Install Docker on VPS |
| Port already in use | `docker compose down` or change port |
