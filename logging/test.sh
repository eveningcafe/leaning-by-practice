#!/bin/bash
# Test script for centralized logging lab

echo "=========================================="
echo "Centralized Logging Lab Test Script"
echo "=========================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo -e "${YELLOW}1. Checking Elasticsearch health...${NC}"
curl -s http://localhost:9200/_cluster/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Status: {d[\"status\"]}, Nodes: {d[\"number_of_nodes\"]}')" 2>/dev/null || echo "Elasticsearch not ready"

echo ""
echo -e "${YELLOW}2. Generating test logs...${NC}"

echo "   - Homepage requests..."
for i in {1..5}; do
    curl -s http://localhost:5000/ > /dev/null
done
echo "     Done: 5 requests to /"

echo "   - User lookups..."
for i in {1..5}; do
    curl -s http://localhost:5000/user/$i > /dev/null
done
echo "     Done: 5 user lookups"

echo "   - Slow requests (warnings)..."
curl -s http://localhost:5000/slow > /dev/null &
curl -s http://localhost:5000/slow > /dev/null &
wait
echo "     Done: 2 slow requests"

echo "   - Error requests..."
for i in {1..3}; do
    curl -s http://localhost:5000/error > /dev/null
done
echo "     Done: 3 errors generated"

echo "   - Random logs..."
curl -s "http://localhost:5000/generate?count=20" > /dev/null
echo "     Done: 20 random logs"

echo ""
echo -e "${YELLOW}3. Checking indices in Elasticsearch...${NC}"
sleep 5  # Wait for Filebeat to ship logs
curl -s http://localhost:9200/_cat/indices?v 2>/dev/null | head -10 || echo "Could not fetch indices"

echo ""
echo -e "${GREEN}=========================================="
echo "Test Complete!"
echo "==========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Open Kibana: http://localhost:5601"
echo "2. Go to Menu → Discover"
echo "3. Create data view with pattern: app-logs-*"
echo "4. Explore your logs!"
echo ""
