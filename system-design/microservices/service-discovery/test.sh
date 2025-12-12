#!/bin/bash
echo "=== Service Discovery (Consul) Test ==="

echo -e "\n1. Check Consul services"
curl -s http://localhost:8500/v1/agent/services | jq

echo -e "\n2. Create user"
curl -s -X POST http://localhost:5001/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice"}' | jq

echo -e "\n3. Create order (discovers user-service via Consul)"
curl -s -X POST http://localhost:5002/orders \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "item": "Book"}' | jq

echo -e "\n4. Check order-service discovery"
curl -s http://localhost:5002/ | jq

echo -e "\n=== Done ==="
echo "Consul UI: http://localhost:8500"
