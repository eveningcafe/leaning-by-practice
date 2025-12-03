#!/bin/bash

echo "=== Session Sharing Test ==="
echo ""

echo "1. Login on app1 (port 5001):"
COOKIE=$(curl -s -c - http://localhost:5001/login/john | tee /dev/tty | grep session_id | awk '{print $7}')
echo ""

echo "2. Access profile from app1:"
curl -s -b "session_id=$COOKIE" http://localhost:5001/profile | jq .
echo ""

echo "3. Access SAME session from app2 (port 5002):"
curl -s -b "session_id=$COOKIE" http://localhost:5002/profile | jq .
echo ""

echo "4. Access SAME session from app3 (port 5003):"
curl -s -b "session_id=$COOKIE" http://localhost:5003/profile | jq .
echo ""

echo "=== Session is shared across all apps! ==="
