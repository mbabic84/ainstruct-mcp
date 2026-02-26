#!/bin/bash
# run_tests.sh - Test runner
# Usage: ./run_tests.sh [options]
#   --unit: Run only unit tests
#   --integration: Run only integration tests
#   --e2e: Run only end-to-end tests

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Default values
TEST_PATH="tests/unit tests/integration tests/e2e"
COMPOSE_FILES="-f docker-compose.yml"
LOG_DIR="test_logs"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --unit)
            TEST_PATH="tests/unit"
            shift
            ;;
        --integration)
            TEST_PATH="tests/integration"
            shift
            ;;
        --e2e)
            TEST_PATH="tests/e2e"
            shift
            ;;
        --help)
            echo "Usage: ./run_tests.sh [options]"
            echo "Options:"
            echo "  --unit         Run only unit tests"
            echo "  --integration  Run only integration tests"
            echo "  --e2e          Run only end-to-end tests"
            echo "  --help         Show this help message"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Create log directory
mkdir -p "$LOG_DIR"

# Build docker compose command
COMPOSE_CMD="docker compose ${COMPOSE_FILES} up --build --abort-on-container-exit --exit-code-from test_runner"

# Run the tests
log_info "Starting tests..."
log_info "Test path: ${TEST_PATH}"
log_info "Logging output to: $LOG_DIR/latest.log"

export TEST_PATH
export DOCKER_BUILDKIT=1
${COMPOSE_CMD} 2>&1 | tee "$LOG_DIR/latest.log"

TEST_EXIT_CODE=${PIPESTATUS[0]}

if [ $TEST_EXIT_CODE -eq 0 ]; then
    log_info "All tests passed!"
    log_info "Log saved to: $LOG_DIR/latest.log"
else
    log_error "Tests failed with exit code: ${TEST_EXIT_CODE}"
    log_info "Full log saved to: $LOG_DIR/latest.log"
fi

exit $TEST_EXIT_CODE
