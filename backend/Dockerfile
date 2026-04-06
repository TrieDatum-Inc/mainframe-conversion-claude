# CardDemo Backend Dockerfile
# Multi-stage build for minimal production image

FROM python:3.11-slim AS base

# System dependencies for psycopg2 and cryptography packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry==1.8.2

# Configure Poetry: no virtualenv inside container
RUN poetry config virtualenvs.create false

# Copy dependency files first (layer caching)
COPY pyproject.toml poetry.lock* ./

# Install production dependencies only
RUN poetry install --without dev --no-interaction --no-ansi

# Copy application code
COPY . .

# Non-root user for security
RUN useradd --create-home --no-log-init appuser
USER appuser

EXPOSE 8000

# Run Alembic migrations then start server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
