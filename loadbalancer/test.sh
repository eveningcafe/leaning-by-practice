#!/bin/bash

echo "=== Nginx Load Balancer Test ==="
echo ""

echo "--- Test 1: Round-Robin Distribution ---"
echo "Sending 6 requests (should rotate: backend1 -> backend2 -> backend3 -> repeat)"
echo ""

for i in {1..6}; do
    echo "Request $i:"
    curl -s http://localhost/ | jq -c .
done

echo ""
echo "--- Test 2: Concurrent Requests ---"
echo "Sending 10 concurrent requests to /heavy endpoint"
echo ""

for i in {1..10}; do
    curl -s http://localhost/heavy &
done | jq -c .
wait

echo ""
echo "--- Test 3: Request Distribution Check ---"
echo "Sending 30 requests, counting distribution:"
echo ""

for i in {1..30}; do
    curl -s http://localhost/
done | jq -r '.server' | sort | uniq -c

echo ""
echo "=== Test Complete ==="
