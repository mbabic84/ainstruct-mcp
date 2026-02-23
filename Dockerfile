FROM python:3.14-alpine

RUN addgroup -g 1000 appgroup && \
    adduser -u 1000 -G appgroup -D appuser

WORKDIR /app

RUN apk add --no-cache curl

# Copy and install Python dependencies as root
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Copy source code
COPY src/ ./src/

# Create data directory and set permissions
RUN mkdir -p /app/data && \
    chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

ENV PYTHONPATH=/app/src

EXPOSE 8000

CMD ["python", "-m", "app.main"]
