FROM python:3.14-slim

# Create non-root user for security best practices
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# Install dependencies as root first
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

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
