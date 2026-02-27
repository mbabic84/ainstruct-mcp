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
    web-ui)
        exec web-ui
        ;;
    *)
        echo "Usage: SERVICE={mcp-server|rest-api|web-ui} $0"
        exit 1
        ;;
esac
