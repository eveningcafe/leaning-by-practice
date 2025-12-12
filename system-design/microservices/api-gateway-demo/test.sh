#!/bin/bash
echo "=== Microservices Test (via API Gateway) ==="

echo -e "\n1. Create user"
curl -s -X POST http://localhost/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice"}' | jq

echo -e "\n2. Create order (calls user-service internally)"
curl -s -X POST http://localhost/orders \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "item": "Book"}' | jq

echo -e "\n3. List users"
curl -s http://localhost/users | jq

echo -e "\n4. List orders"
curl -s http://localhost/orders | jq

echo -e "\n=== Done ==="
