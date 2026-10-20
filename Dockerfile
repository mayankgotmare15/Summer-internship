# Multi-stage production Dockerfile for RouteDesk
FROM python:3.10-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Pre-download required NLTK corpora during build stage
RUN python -c "import nltk; nltk.download('stopwords'); nltk.download('wordnet'); nltk.download('punkt'); nltk.download('punkt_tab'); nltk.download('omw-1.4')"

# Production runtime stage
FROM python:3.10-slim AS runner

WORKDIR /app

# Create a non-root group and user
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

# Copy installed python packages from builder
COPY --from=builder /root/.local /home/appuser/.local
COPY --from=builder /root/nltk_data /home/appuser/nltk_data
ENV PATH=/home/appuser/.local/bin:$PATH
ENV NLTK_DATA=/home/appuser/nltk_data

# Set runtime environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    MODEL_DIR=/app/artifacts/bundle

# Copy application source and configurations
COPY --chown=appuser:appgroup src/ /app/src/
COPY --chown=appuser:appgroup configs/ /app/configs/
COPY --chown=appuser:appgroup models/ /app/models/
COPY --chown=appuser:appgroup pyproject.toml alembic.ini* /app/

# Create runtime directories with appropriate permissions
RUN mkdir -p /app/local_db /app/artifacts/bundle /app/reports && \
    chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
