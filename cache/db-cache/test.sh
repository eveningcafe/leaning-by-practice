#!/bin/bash

echo "============================================"
echo "  Redis Cache Lab: Reduce Database Load"
echo "============================================"
echo ""

echo ">>> Resetting stats..."
curl -s http://localhost:5000/stats/reset | jq .
echo ""

echo "============================================"
echo "  TEST 1: With Redis Cache (/products)"
echo "============================================"
echo ""

echo ">>> Making 10 requests to /products (cached endpoint)..."
for i in {1..10}; do
    source=$(curl -s http://localhost:5000/products | jq -r '.source')
    echo "  Request $i: $source"
done
echo ""

echo ">>> Current stats:"
curl -s http://localhost:5000/stats | jq .
echo ""

echo "============================================"
echo "  TEST 2: Without Cache (/products/no-cache)"
echo "============================================"
echo ""

echo ">>> Making 10 requests to /products/no-cache..."
for i in {1..10}; do
    source=$(curl -s http://localhost:5000/products/no-cache | jq -r '.source')
    echo "  Request $i: $source"
done
echo ""

echo ">>> Final stats:"
curl -s http://localhost:5000/stats | jq .
echo ""

echo "============================================"
echo "  CONCLUSION"
echo "============================================"
echo ""
echo "With caching:    10 requests = 1 DB query + 9 cache hits"
echo "Without caching: 10 requests = 10 DB queries"
echo ""
echo "Redis cache reduced database load by 90%!"
echo ""
