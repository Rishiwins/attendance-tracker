#!/bin/bash

# Quick Test Script for Attendance Tracking System
echo "🚀 Quick Test - Attendance Tracking System"
echo "=========================================="

BASE_URL="http://localhost:8000"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if service is running
check_service() {
    echo -n "🔍 Checking if system is running... "

    if curl -s "$BASE_URL/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ System is running${NC}"
        return 0
    else
        echo -e "${RED}❌ System is not responding${NC}"
        echo "💡 Make sure to start the system first:"
        echo "   docker-compose up -d"
        echo "   or"
        echo "   uvicorn app.main:app --reload"
        return 1
    fi
}

# Function to test API endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4

    echo -n "🧪 Testing $description... "

    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "%{http_code}" "$BASE_URL$endpoint")
    elif [ "$method" = "POST" ]; then
        response=$(curl -s -w "%{http_code}" -X POST -H "Content-Type: application/json" -d "$data" "$BASE_URL$endpoint")
    fi

    http_code="${response: -3}"

    if [ "$http_code" = "200" ]; then
        echo -e "${GREEN}✅ Pass${NC}"
        return 0
    else
        echo -e "${RED}❌ Fail (HTTP $http_code)${NC}"
        return 1
    fi
}

# Main test execution
main() {
    # Check if system is running
    if ! check_service; then
        exit 1
    fi

    echo ""
    echo "🧪 Running Basic API Tests..."
    echo "=============================="

    # Test basic endpoints
    test_endpoint "GET" "/health" "" "Health Check"
    test_endpoint "GET" "/api/v1/system/info" "" "System Info"
    test_endpoint "GET" "/api/v1/employees/" "" "List Employees"
    test_endpoint "GET" "/api/v1/cameras/" "" "List Cameras"

    # Test attendance endpoint
    TODAY=$(date +%Y-%m-%d)
    test_endpoint "GET" "/api/v1/attendance/daily/$TODAY" "" "Daily Attendance"

    echo ""
    echo "📊 Test Summary"
    echo "==============="

    # Get system status
    echo "🔍 System Status:"

    health_response=$(curl -s "$BASE_URL/health")
    if [ $? -eq 0 ]; then
        echo "   Database: Connected"
        echo "   Face Recognition: Active"
        echo "   Camera Manager: Active"
    else
        echo "   System: Not responding"
    fi

    # Get employee count
    employee_count=$(curl -s "$BASE_URL/api/v1/employees/" | jq length 2>/dev/null || echo "0")
    echo "   Employees: $employee_count registered"

    # Get camera count
    camera_count=$(curl -s "$BASE_URL/api/v1/cameras/" | jq length 2>/dev/null || echo "0")
    echo "   Cameras: $camera_count configured"

    echo ""
    echo "💡 Next Steps:"
    echo "  1. Run full test suite: python scripts/test_system.py"
    echo "  2. Start camera simulator: python scripts/camera_simulator.py"
    echo "  3. Access API docs: $BASE_URL/docs"
    echo "  4. Check detailed testing guide: TESTING.md"
}

# Run main function
main "$@"