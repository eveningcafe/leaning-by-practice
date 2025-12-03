# Reverse Proxy Lab (Nginx + SSL Termination)

Nginx as a reverse proxy with SSL termination - handles HTTPS, forwards plain HTTP to backends.

## How It Works

```
Without Reverse Proxy:
        Client ──HTTP──▶ Backend (insecure, exposed directly)

With Reverse Proxy + SSL Termination:
        Client ══HTTPS══▶ Nginx ──HTTP──▶ Backend1/2/3
                          (SSL)           (internal, safe)

Benefits:
  ✓ Encrypted traffic between client and server
  ✓ Backends don't need SSL configuration
  ✓ Single place to manage certificates
  ✓ Security headers added at proxy level
  ✓ Load balancing included
```

```nginx
# nginx.conf - SSL Termination
server {
    listen 443 ssl;

    # SSL Certificate
    ssl_certificate     /etc/nginx/certs/server.crt;
    ssl_certificate_key /etc/nginx/certs/server.key;

    # Forward to backend (plain HTTP internally)
    location / {
        proxy_pass http://backends;
        proxy_set_header X-Forwarded-Proto $scheme;  # Tell backend it's HTTPS
    }
}
```

## Setup & Run

### Step 1: Generate Self-Signed Certificate

```bash
cd reverse-proxy
chmod +x generate-cert.sh
./generate-cert.sh
```

This creates:
- `certs/server.key` - Private key
- `certs/server.crt` - Certificate

### Step 2: Run the Lab

```bash
docker compose up --build
```

### Step 3: Test

```bash
chmod +x test.sh && ./test.sh
```

## Endpoints

| URL | Description |
|-----|-------------|
| http://localhost | Redirects to HTTPS |
| https://localhost | Main endpoint (shows client info) |
| https://localhost/secure-data | Simulated secure endpoint |
| https://localhost/health | Health check |

## Test Manually

```bash
# 1. HTTP redirects to HTTPS
curl -I http://localhost
# → 301 Moved Permanently → https://localhost/

# 2. HTTPS works (-k skips cert verification for self-signed)
curl -sk https://localhost/ | jq .
# → Shows server info and X-Forwarded-Proto: https

# 3. Secure endpoint
curl -sk https://localhost/secure-data | jq .
# → Shows that SSL was terminated at Nginx

# 4. View certificate info
echo | openssl s_client -connect localhost:443 2>/dev/null | openssl x509 -noout -text

# 5. Test in browser
# Open https://localhost
# Click "Advanced" → "Proceed to localhost" (bypass self-signed warning)
```

---

## SSL Certificate Options

### Option 1: Self-Signed (Development Only)

```bash
./generate-cert.sh
```

**Pros:** Free, instant, no domain needed
**Cons:** Browser warnings, not trusted by clients

**Use for:** Local development, testing

---

### Option 2: Let's Encrypt (Free, Production)

Free certificates from Let's Encrypt using Certbot.

**Requirements:**
- Own a domain (e.g., `example.com`)
- Domain points to your server's IP
- Port 80 accessible for verification

```bash
# Install certbot
sudo apt install certbot

# Generate certificate (standalone mode)
sudo certbot certonly --standalone -d example.com -d www.example.com

# Certificates saved to:
#   /etc/letsencrypt/live/example.com/fullchain.pem
#   /etc/letsencrypt/live/example.com/privkey.pem
```

**Update nginx.conf:**

```nginx
ssl_certificate     /etc/letsencrypt/live/example.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
```

**Auto-renewal:**

```bash
# Test renewal
sudo certbot renew --dry-run

# Add to crontab (runs twice daily)
0 0,12 * * * certbot renew --quiet
```

**Pros:** Free, trusted by all browsers, auto-renewal
**Cons:** Requires domain, 90-day expiry (auto-renew)

---

### Option 3: CA-Signed Certificate (Paid, Enterprise)

Buy from Certificate Authorities: DigiCert, Comodo, GoDaddy, etc.

**Steps:**

1. **Generate CSR (Certificate Signing Request):**

```bash
openssl req -new -newkey rsa:2048 -nodes \
    -keyout example.com.key \
    -out example.com.csr \
    -subj "/C=US/ST=State/L=City/O=Company/CN=example.com"
```

2. **Submit CSR to CA:**
   - Go to CA website (DigiCert, Comodo, etc.)
   - Purchase certificate
   - Upload the `.csr` file
   - Complete domain verification (email, DNS, or HTTP)

3. **Download certificate files:**
   - `example.com.crt` - Your certificate
   - `ca-bundle.crt` - CA chain (intermediate certificates)

4. **Combine into fullchain:**

```bash
cat example.com.crt ca-bundle.crt > fullchain.crt
```

5. **Update nginx.conf:**

```nginx
ssl_certificate     /etc/nginx/certs/fullchain.crt;
ssl_certificate_key /etc/nginx/certs/example.com.key;
```

**Pros:** Extended validation (EV), warranty, support, longer validity (1-2 years)
**Cons:** Costs money ($10-$500+/year)

---

## Comparison Table

| Type | Cost | Trust | Validity | Best For |
|------|------|-------|----------|----------|
| Self-Signed | Free | ❌ Browser warning | Any | Development |
| Let's Encrypt | Free | ✅ All browsers | 90 days | Production (most cases) |
| CA-Signed | $10-500+/yr | ✅ All browsers + EV | 1-2 years | Enterprise, e-commerce |

---

## Security Headers Explained

```nginx
# Prevent clickjacking
add_header X-Frame-Options "SAMEORIGIN";

# Prevent MIME type sniffing
add_header X-Content-Type-Options "nosniff";

# Enable XSS filter
add_header X-XSS-Protection "1; mode=block";

# Force HTTPS for 1 year
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
```

## Key Takeaway

```
SSL Termination at Reverse Proxy:
  - Client ↔ Nginx: HTTPS (encrypted)
  - Nginx ↔ Backend: HTTP (internal network, fast)

Benefits:
  - Centralized SSL management
  - Backends stay simple (no SSL config)
  - Easy certificate rotation
  - Security headers in one place
```
