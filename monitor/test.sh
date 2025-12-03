#!/bin/bash

echo "============================================"
echo "  Monitor Lab: Health Checks & Alerts"
echo "============================================"
echo ""

echo ">>> Testing load balancer (round-robin)..."
for i in {1..6}; do
    server=$(curl -s http://localhost:80/ | jq -r '.server')
    echo "  Request $i: $server"
done
echo ""

echo ">>> Checking Prometheus targets..."
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {instance: .labels.instance, health: .health}'
echo ""

echo "============================================"
echo "  Test Alert: Kill a backend container"
echo "============================================"
echo ""
echo "Run this command to kill backend1:"
echo "  docker compose stop backend1"
echo ""
echo "Then check:"
echo "  - Prometheus alerts: http://localhost:9090/alerts"
echo "  - Alertmanager: http://localhost:9093"
echo "  - Your Telegram for the alert message!"
echo ""
echo "Bring it back with:"
echo "  docker compose start backend1"
echo ""
