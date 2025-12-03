#!/bin/bash

echo "============================================"
echo "  Reverse Proxy Lab: SSL Termination"
echo "============================================"
echo ""

echo ">>> Test HTTP redirect to HTTPS..."
curl -sI http://localhost | head -3
echo ""

echo ">>> Test HTTPS endpoint (skip cert verification for self-signed)..."
curl -sk https://localhost/ | jq .
echo ""

echo ">>> Test secure-data endpoint..."
curl -sk https://localhost/secure-data | jq .
echo ""

echo ">>> Test round-robin load balancing..."
echo "Making 6 requests:"
for i in {1..6}; do
    server=$(curl -sk https://localhost/ | jq -r '.server')
    echo "  Request $i: $server"
done
echo ""

echo "============================================"
echo "  SSL Certificate Info"
echo "============================================"
echo ""
echo ">>> Certificate details:"
echo | openssl s_client -connect localhost:443 2>/dev/null | openssl x509 -noout -subject -dates
echo ""
