#!/bin/bash
#
# Start all data synchronization services
# Usage: ./start_sync_services.sh [command]
#
# Commands:
#   worker  - Start Celery worker
#   beat    - Start Celery beat scheduler
#   flower  - Start Flower web UI
#   all     - Start all services (worker + beat)
#

set -e

BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BACKEND_DIR"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Redis is running
check_redis() {
    if ! redis-cli ping > /dev/null 2>&1; then
        echo -e "${RED}Error: Redis is not running${NC}"
        echo "Start Redis with: brew services start redis"
        echo "Or run manually: redis-server"
        exit 1
    fi
    echo -e "${GREEN}✓ Redis is running${NC}"
}

# Start Celery worker
start_worker() {
    echo -e "${YELLOW}Starting Celery worker...${NC}"
    celery -A celery_app:celery_app worker \
        --loglevel=info \
        --queues=sync,validation,maintenance \
        --concurrency=4 \
        --max-tasks-per-child=1000
}

# Start Celery beat scheduler
start_beat() {
    echo -e "${YELLOW}Starting Celery beat scheduler...${NC}"
    celery -A celery_app:celery_app beat \
        --loglevel=info \
        --scheduler=celery.beat.PersistentScheduler
}

# Start Flower web UI
start_flower() {
    echo -e "${YELLOW}Starting Flower web UI...${NC}"
    echo -e "${GREEN}Access Flower at: http://localhost:5555${NC}"
    celery -A celery_app:celery_app flower \
        --port=5555
}

# Start all services
start_all() {
    echo -e "${YELLOW}Starting all sync services...${NC}"

    # Start worker in background
    celery -A celery_app:celery_app worker \
        --loglevel=info \
        --queues=sync,validation,maintenance \
        --concurrency=4 \
        --max-tasks-per-child=1000 \
        --detach \
        --pidfile=/tmp/celery_worker.pid \
        --logfile=/tmp/celery_worker.log

    # Start beat in background
    celery -A celery_app:celery_app beat \
        --loglevel=info \
        --scheduler=celery.beat.PersistentScheduler \
        --detach \
        --pidfile=/tmp/celery_beat.pid \
        --logfile=/tmp/celery_beat.log

    echo -e "${GREEN}✓ Services started${NC}"
    echo "Worker PID file: /tmp/celery_worker.pid"
    echo "Beat PID file: /tmp/celery_beat.pid"
    echo "Worker log: /tmp/celery_worker.log"
    echo "Beat log: /tmp/celery_beat.log"
    echo ""
    echo "To stop services, run: ./stop_sync_services.sh"
}

# Show help
show_help() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  worker  - Start Celery worker (foreground)"
    echo "  beat    - Start Celery beat scheduler (foreground)"
    echo "  flower  - Start Flower web UI (foreground)"
    echo "  all     - Start all services (background)"
    echo "  help    - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 worker  # Start worker in foreground"
    echo "  $0 all     # Start all services in background"
    echo ""
}

# Main
main() {
    check_redis

    case "${1:-help}" in
        worker)
            start_worker
            ;;
        beat)
            start_beat
            ;;
        flower)
            start_flower
            ;;
        all)
            start_all
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}Unknown command: $1${NC}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

main "$@"
