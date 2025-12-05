# Git CI Lab (GitHub Actions)

## References

- [GitHub Actions Official Docs](https://docs.github.com/en/actions)
- [Workflow Syntax Reference](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
- [Actions Marketplace](https://github.com/marketplace?type=actions)

---

## What is CI?

```
Developer pushes code → GitHub Actions runs → Build & Test automatically
                                            ↓
                                    Pass ✓ or Fail ✗
```

---

## Project Structure

```
myproject/
├── .github/
│   └── workflows/
│       └── ci.yml        # GitHub Actions config
├── app.py                # Simple Python app
├── test_app.py           # Tests
└── requirements.txt      # Dependencies (optional)
```

---

## Step 1: Create Simple App

```bash
mkdir myproject && cd myproject

# app.py
cat > app.py << 'EOF'
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

if __name__ == "__main__":
    print(add(1, 2))
EOF
```

---

## Step 2: Create Tests

```bash
# test_app.py
cat > test_app.py << 'EOF'
from app import add, subtract

def test_add():
    assert add(1, 2) == 3
    assert add(-1, 1) == 0

def test_subtract():
    assert subtract(5, 3) == 2
    assert subtract(0, 0) == 0
EOF
```

---

## Step 3: Create GitHub Actions Workflow

```bash
mkdir -p .github/workflows

# .github/workflows/ci.yml
cat > .github/workflows/ci.yml << 'EOF'
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install pytest

      - name: Run tests
        run: pytest test_app.py -v
EOF
```

---

## Step 4: Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit with CI"

# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/myproject.git
git push -u origin main
```

---

## What Happens

1. You push code to GitHub
2. GitHub Actions detects `.github/workflows/ci.yml`
3. Runs the workflow:
   - Checkout code
   - Setup Python 3.11
   - Install pytest
   - Run tests
4. Shows ✓ (pass) or ✗ (fail) on your commit

---

## View Results

Go to your repo → **Actions** tab → See workflow runs

```
✓ CI - Initial commit with CI
  └── test
      ├── Set up job
      ├── Checkout
      ├── Set up Python
      ├── Install dependencies
      ├── Run tests          ← test_add PASSED, test_subtract PASSED
      └── Complete job
```

---

## Make It Fail (Demo)

```bash
# Break the test
echo "def add(a, b): return a - b  # BUG!" > app.py
git commit -am "Introduce bug"
git push
```

GitHub Actions will show:
```
✗ CI - Introduce bug
  └── test
      └── Run tests: FAILED
          test_add FAILED: assert -1 == 3
```

---

## Workflow Syntax Reference

```yaml
name: CI                    # Workflow name

on:                         # Triggers
  push:
    branches: [main]        # Run on push to main
  pull_request:
    branches: [main]        # Run on PR to main

jobs:
  test:                     # Job name
    runs-on: ubuntu-latest  # Runner OS

    steps:
      - uses: actions/checkout@v4           # Clone repo
      - uses: actions/setup-python@v5       # Setup Python
        with:
          python-version: '3.11'
      - run: pip install pytest             # Shell command
      - run: pytest test_app.py -v          # Run tests
```

---

## Common Triggers

```yaml
on:
  push:                     # On any push
  pull_request:             # On PR
  schedule:
    - cron: '0 0 * * *'     # Daily at midnight
  workflow_dispatch:        # Manual trigger button
```

---

## Add Build Step (Optional)

```yaml
jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install pytest
          pip install -r requirements.txt || true

      - name: Lint (optional)
        run: |
          pip install flake8
          flake8 app.py --max-line-length=120 || true

      - name: Run tests
        run: pytest test_app.py -v

      - name: Build check
        run: python -m py_compile app.py
```

---

## Using Secrets (Advanced)

Never put passwords/tokens in code. Use GitHub Secrets instead.

### Step 1: Add Secret in GitHub

```
GitHub Repo → Settings → Secrets and variables → Actions → New repository secret

Name: MY_API_KEY
Value: abc123secret
```

### Step 2: Use Secret in Workflow

```yaml
name: CI with Secrets

on: [push]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Use secret
        env:
          API_KEY: ${{ secrets.MY_API_KEY }}
        run: |
          echo "Using API key..."
          # $API_KEY is available here (hidden in logs)
          python app.py
```

### Step 3: Use in Python

```python
import os

api_key = os.environ.get('API_KEY')
print(f"Key exists: {api_key is not None}")  # Never print actual key!
```

### Common Secrets

| Secret Name | Usage |
|-------------|-------|
| `DOCKER_USERNAME` | Docker Hub login |
| `DOCKER_PASSWORD` | Docker Hub password |
| `AWS_ACCESS_KEY_ID` | AWS credentials |
| `AWS_SECRET_ACCESS_KEY` | AWS credentials |
| `SSH_PRIVATE_KEY` | Deploy via SSH |

### Example: Deploy with Docker Hub

```yaml
name: Build and Push

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Login to Docker Hub
        run: echo "${{ secrets.DOCKER_PASSWORD }}" | docker login -u "${{ secrets.DOCKER_USERNAME }}" --password-stdin

      - name: Build and push
        run: |
          docker build -t myuser/myapp:latest .
          docker push myuser/myapp:latest
```

### Security Notes

- Secrets are hidden in logs (shows `***`)
- Secrets not available in forks (for security)
- Use `secrets.GITHUB_TOKEN` for GitHub API (auto-provided)

---

## Quick Setup Script

```bash
#!/bin/bash
mkdir -p myproject/.github/workflows && cd myproject

# App
echo 'def add(a, b): return a + b' > app.py

# Test
echo 'from app import add
def test_add(): assert add(1, 2) == 3' > test_app.py

# CI
cat > .github/workflows/ci.yml << 'EOF'
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install pytest
      - run: pytest -v
EOF

git init && git add . && git commit -m "Initial with CI"
echo "Done! Push to GitHub to see CI in action."
```
