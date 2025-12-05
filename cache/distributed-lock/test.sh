#!/bin/bash

echo "============================================"
echo "  Redis Distributed Lock: Race Condition Demo"
echo "============================================"
echo ""

echo ">>> Resetting stock to 100 units..."
curl -s http://localhost:5001/stock/reset | jq .
echo ""

echo "============================================"
echo "  TEST 1: WITHOUT Lock (Race Condition!)"
echo "============================================"
echo ""
echo ">>> Sending 20 concurrent purchases to 3 apps WITHOUT lock..."
echo ""

# Send concurrent requests without lock
for i in {1..20}; do
    port=$((5001 + (i % 3)))
    curl -s http://localhost:$port/buy/no-lock > /dev/null &
done
wait

echo ">>> Results (no lock):"
curl -s http://localhost:5001/stats | jq .
echo ""

# Check for race conditions
RACE=$(curl -s http://localhost:5001/stats | jq '.race_conditions_detected')
MATCH=$(curl -s http://localhost:5001/stats | jq '.stock_matches_expected')

if [ "$RACE" -gt 0 ]; then
    echo "!!! RACE CONDITION DETECTED: Stock went negative $RACE times!"
fi
if [ "$MATCH" == "false" ]; then
    echo "!!! STOCK MISMATCH: Actual stock != expected stock"
fi
echo ""

echo "============================================"
echo "  TEST 2: WITH Lock (Safe)"
echo "============================================"
echo ""

echo ">>> Resetting stock to 100 units..."
curl -s http://localhost:5001/stock/reset | jq .
echo ""

echo ">>> Sending 20 concurrent purchases to 3 apps WITH lock..."
echo ""

# Send concurrent requests with lock (using retry endpoint for resilience)
for i in {1..20}; do
    port=$((5001 + (i % 3)))
    curl -s http://localhost:$port/buy/with-lock-retry > /dev/null &
done
wait

echo ">>> Results (with lock):"
curl -s http://localhost:5001/stats | jq .
echo ""

RACE=$(curl -s http://localhost:5001/stats | jq '.race_conditions_detected')
MATCH=$(curl -s http://localhost:5001/stats | jq '.stock_matches_expected')

if [ "$RACE" -eq 0 ] && [ "$MATCH" == "true" ]; then
    echo "SUCCESS: No race conditions! Stock is accurate."
fi
echo ""

echo "============================================"
echo "  CONCLUSION"
echo "============================================"
echo ""
echo "Without lock: Race conditions cause overselling/stock mismatch"
echo "With lock:    Only one purchase processed at a time, stock is accurate"
echo ""
