#!/bin/bash

echo "=== DB Cache Test ==="
echo ""

echo "1. Query WITHOUT cache (hits DB every time):"
curl -s http://localhost:5000/products/no-cache | jq .
echo ""

echo "2. Clear cache and query WITH cache (first hit - goes to DB):"
curl -s http://localhost:5000/clear-cache > /dev/null
curl -s http://localhost:5000/products/cached | jq .
echo ""

echo "3. Query WITH cache again (hits Redis - much faster!):"
curl -s http://localhost:5000/products/cached | jq .
echo ""

echo "=== Compare 'time_ms' field between requests ==="
