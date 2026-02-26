#!/bin/sh
# Entrypoint script for ainstruct-mcp services
# Usage: docker run <image> [options]
#   --mcp    Start MCP server (default)
#   --rest   Start REST API server
#   --help   Show this help message

set -e

# Default to MCP server if no arguments
if [ $# -eq 0 ]; then
    set -- --mcp
fi

case "$1" in
    --mcp)
        echo "Starting MCP server..."
        exec python -m app.main
        ;;
    --rest)
        echo "Starting REST API server..."
        exec python -m app.rest.run
        ;;
    --help)
        echo "Usage: $0 [options]"
        echo "Options:"
        echo "  --mcp    Start MCP server (default)"
        echo "  --rest   Start REST API server"
        echo "  --help   Show this help message"
        exit 0
        ;;
    *)
        echo "Unknown option: $1"
        echo "Use --help for usage information"
        exit 1
        ;;
esac
