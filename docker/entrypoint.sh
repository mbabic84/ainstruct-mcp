#!/bin/sh
set -e

. /app/.venv/bin/activate

case "$SERVICE" in
    mcp-server)
        exec mcp-server
        ;;
    rest-api)
        exec rest-api
        ;;
    *)
        echo "Usage: SERVICE={mcp-server|rest-api} $0"
        exit 1
        ;;
esac
