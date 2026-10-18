# ==============================================================================
# Hardened, Multi-Stage Production Dockerfile for IT Ticket Classifier API
# Security Controls:
# - Minimal base image (python:3.10-slim)
# - Dedicated unprivileged user (appuser:1000)
# - No root execution; no sensitive build secrets baked into layers
# - Built-in healthcheck probe
# ==============================================================================

FROM python:3.10-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final Runtime Stage
FROM python:3.10-slim AS runner

WORKDIR /app

# Install curl for container health check
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create unprivileged application user
RUN useradd -m -u 1000 appuser

# Copy installed python packages from builder
COPY --from=builder /root/.local /home/appuser/.local

# Ensure local user path is on PATH
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Copy project source code and configurations
COPY configs/ /app/configs/
COPY src/ /app/src/
COPY models/ /app/models/
COPY ui/ /app/ui/

# Set up runtime directories and file permissions for unprivileged user
RUN mkdir -p /app/data/monitoring /app/models \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "src.serving.app:app", "--host", "0.0.0.0", "--port", "8000"]
