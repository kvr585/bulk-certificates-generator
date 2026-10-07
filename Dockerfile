# Multi-stage production Dockerfile
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies if needed
RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final runtime image
FROM python:3.12-slim

# System dependencies for ReportLab (freetype, fontconfig)
RUN apt-get update && apt-get install --no-install-recommends -y \
    libfreetype6 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Copy application files
COPY app/ /app/app/
COPY scripts/ /app/scripts/
COPY .env.example /app/.env

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/generated_certificates && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
