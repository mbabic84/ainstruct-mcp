#!/bin/bash
# Run tests in Docker for consistent local and CI testing

set -e

echo "Building test image..."
docker build -f Dockerfile.test -t ainstruct-test .

echo "Running tests..."
docker run --rm ainstruct-test
