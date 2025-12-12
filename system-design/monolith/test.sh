#!/bin/bash
echo "=== Monolith Test ==="

echo -e "\n1. Create user"
curl -s -X POST http://localhost:5000/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice"}' | jq

echo -e "\n2. Create order for user"
curl -s -X POST http://localhost:5000/orders \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "item": "Book"}' | jq

echo -e "\n3. List users"
curl -s http://localhost:5000/users | jq

echo -e "\n4. List orders"
curl -s http://localhost:5000/orders | jq

echo -e "\n=== Done ==="
