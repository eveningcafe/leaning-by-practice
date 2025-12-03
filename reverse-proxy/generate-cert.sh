#!/bin/bash

# Generate self-signed SSL certificate for development/testing
# DO NOT use in production - use CA-signed certificates instead

CERT_DIR="./certs"
DOMAIN="localhost"

echo "============================================"
echo "  Generating Self-Signed SSL Certificate"
echo "============================================"
echo ""

# Create certs directory if not exists
mkdir -p $CERT_DIR

# Generate private key and certificate in one command
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout $CERT_DIR/server.key \
    -out $CERT_DIR/server.crt \
    -subj "/C=US/ST=State/L=City/O=Development/CN=$DOMAIN" \
    -addext "subjectAltName=DNS:localhost,DNS:*.localhost,IP:127.0.0.1"

echo ""
echo "✅ Certificate generated successfully!"
echo ""
echo "Files created:"
echo "  - $CERT_DIR/server.key (Private Key)"
echo "  - $CERT_DIR/server.crt (Certificate)"
echo ""
echo "⚠️  This is a SELF-SIGNED certificate!"
echo "   Your browser will show a security warning."
echo "   Click 'Advanced' → 'Proceed to localhost' to continue."
echo ""
