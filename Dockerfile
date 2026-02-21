from python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

RUN mkdir -p /app/data

COPY src/ ./src/

ENV PYTHONPATH=/app/src

EXPOSE 8000

CMD ["python", "-m", "app.main"]
