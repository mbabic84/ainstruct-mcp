#!/bin/sh
set -e

case "$SERVICE" in
    mcp-server)
        exec uv run mcp-server
        ;;
    rest-api)
        exec uv run rest-api
        ;;
    *)
        echo "Usage: SERVICE={mcp-server|rest-api} $0"
        exit 1
        ;;
esac
