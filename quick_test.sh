#!/bin/bash
# Schneller Test aller Komponenten

set -e

echo "╔═══════════════════════════════════════╗"
echo "║   KI-System Quick Test Suite         ║"
echo "╚═══════════════════════════════════════╝"
echo ""

# Farben
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test-Counter
PASSED=0
FAILED=0

# Funktion für Tests
run_test() {
    local test_name="$1"
    local test_command="$2"

    echo -n "Testing ${test_name}... "

    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        ((FAILED++))
        return 1
    fi
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. Environment Checks"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

run_test "Python 3" "python3 --version"
run_test "Virtual Environment" "test -d venv"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. Dependencies"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Aktiviere venv falls vorhanden
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

run_test "loguru" "python3 -c 'import loguru'"
run_test "numpy" "python3 -c 'import numpy'"
run_test "pandas" "python3 -c 'import pandas'"
run_test "scikit-learn" "python3 -c 'import sklearn'"
run_test "sqlite3" "python3 -c 'import sqlite3'"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. Project Structure"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

run_test "src/ directory" "test -d src"
run_test "config/ directory" "test -d config"
run_test "main.py exists" "test -f main.py"
run_test "config.yaml exists" "test -f config/config.yaml"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. Module Imports"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

run_test "utils.database" "python3 -c 'from src.utils.database import Database'"
run_test "utils.config_loader" "python3 -c 'from src.utils.config_loader import ConfigLoader'"
run_test "platform_factory" "python3 -c 'from src.data_collector.platform_factory import PlatformFactory'"
run_test "lighting_model" "python3 -c 'from src.models.lighting_model import LightingModel'"
run_test "decision_engine" "python3 -c 'from src.decision_engine.engine import DecisionEngine'"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5. Database"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

run_test "Database test" "python3 test_database.py"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6. Configuration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f ".env" ]; then
    run_test ".env file" "test -f .env"

    # Optional: Teste ob .env gültige Werte hat (aber zeige keine Secrets)
    if grep -q "PLATFORM_TYPE=" .env; then
        echo -e "  ${GREEN}✓${NC} PLATFORM_TYPE configured"
    else
        echo -e "  ${YELLOW}⚠${NC} PLATFORM_TYPE not set"
    fi
else
    echo -e "  ${YELLOW}⚠ SKIP${NC} .env not found (expected for first setup)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Test Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "Passed: ${GREEN}${PASSED}${NC}"
echo -e "Failed: ${RED}${FAILED}${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}╔═══════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║   ✓ ALL TESTS PASSED!                ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════╝${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Configure .env with your credentials"
    echo "  2. Run: python3 main.py test"
    echo "  3. Run: python3 main.py status"
    exit 0
else
    echo -e "${RED}╔═══════════════════════════════════════╗${NC}"
    echo -e "${RED}║   ✗ SOME TESTS FAILED                ║${NC}"
    echo -e "${RED}╚═══════════════════════════════════════╝${NC}"
    echo ""
    echo "Please check:"
    echo "  1. Virtual environment: source venv/bin/activate"
    echo "  2. Dependencies: pip install -r requirements.txt"
    echo "  3. See TESTING.md for detailed troubleshooting"
    exit 1
fi
