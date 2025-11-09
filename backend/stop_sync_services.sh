#!/bin/bash
#
# Stop all data synchronization services
# Usage: ./stop_sync_services.sh
#

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

WORKER_PID_FILE="/tmp/celery_worker.pid"
BEAT_PID_FILE="/tmp/celery_beat.pid"

echo -e "${YELLOW}Stopping sync services...${NC}"

# Stop worker
if [ -f "$WORKER_PID_FILE" ]; then
    WORKER_PID=$(cat "$WORKER_PID_FILE")
    if kill -0 "$WORKER_PID" 2>/dev/null; then
        echo "Stopping worker (PID: $WORKER_PID)"
        kill "$WORKER_PID"
        rm "$WORKER_PID_FILE"
        echo -e "${GREEN}✓ Worker stopped${NC}"
    else
        echo "Worker not running (stale PID file)"
        rm "$WORKER_PID_FILE"
    fi
else
    echo "No worker PID file found"
fi

# Stop beat
if [ -f "$BEAT_PID_FILE" ]; then
    BEAT_PID=$(cat "$BEAT_PID_FILE")
    if kill -0 "$BEAT_PID" 2>/dev/null; then
        echo "Stopping beat (PID: $BEAT_PID)"
        kill "$BEAT_PID"
        rm "$BEAT_PID_FILE"
        echo -e "${GREEN}✓ Beat stopped${NC}"
    else
        echo "Beat not running (stale PID file)"
        rm "$BEAT_PID_FILE"
    fi
else
    echo "No beat PID file found"
fi

# Kill any remaining celery processes
if pgrep -f "celery.*worker" > /dev/null; then
    echo -e "${YELLOW}Killing remaining celery worker processes...${NC}"
    pkill -f "celery.*worker"
fi

if pgrep -f "celery.*beat" > /dev/null; then
    echo -e "${YELLOW}Killing remaining celery beat processes...${NC}"
    pkill -f "celery.*beat"
fi

echo -e "${GREEN}✓ All sync services stopped${NC}"
