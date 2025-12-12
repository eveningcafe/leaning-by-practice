#!/bin/bash
echo "=== Clean Architecture Test ==="

echo -e "\n1. Create user"
curl -s -X POST http://localhost:5001/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Bob", "email": "bob@test.com"}' | jq

echo -e "\n2. List users"
curl -s http://localhost:5001/users | jq

echo -e "\n3. Get user by ID"
curl -s http://localhost:5001/users/1 | jq

echo -e "\n4. Delete user"
curl -s -X DELETE http://localhost:5001/users/1 | jq

echo -e "\n=== Done ==="
